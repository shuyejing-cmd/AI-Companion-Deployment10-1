from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from langchain.chains import LLMChain
from langchain.prompts import (
    ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
)
from typing import AsyncGenerator
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.memory_manager import MemoryManager
from app.crud import crud_message, crud_companion
from app.schemas.message import MessageCreate
import redis.asyncio as redis
from app.services.rag_service import rag_service
from app.services.intent_analyzer import intent_analyzer_service

class ChatService:
    def __init__(self, db: AsyncSession, redis_client: redis.Redis, companion_id: UUID, user_id: UUID):
        self.db = db
        self.redis_client = redis_client
        self.user_id = user_id
        self.companion_id = companion_id
        self.memory_manager = MemoryManager(
            redis_client=self.redis_client,
            companion_name=str(companion_id),
            user_id=str(self.user_id),
            ai_prefix="AI",
        )

    async def process_user_message(self, user_message: str) -> AsyncGenerator[str, None]:
        """处理单条用户消息的完整流程，并在每次处理时获取最新的伙伴人设。"""
        
        companion = await crud_companion.get_companion_by_id(db=self.db, companion_id=self.companion_id)
        if not companion:
            yield "[ERROR] 伙伴信息不存在，对话无法继续。"
            yield "[END_OF_STREAM]"
            return
        
        self.memory_manager.ai_prefix = companion.name

        memory = await self.memory_manager.get_memory()
        history_messages = [f"[{'user' if msg.type == 'human' else 'assistant'}] {msg.content}" for msg in memory.chat_memory.messages]

        ai_partner_persona = f"人设名称: {companion.name}\n核心指令: {companion.instructions}"
        intent_analysis_result = await intent_analyzer_service.analyze(
            user_message=user_message,
            chat_history=history_messages,
            ai_partner_persona=ai_partner_persona
        )

        if intent_analysis_result.confidence < 0.4:
            final_strategy_prompt = """
# 行动策略
注意：你对用户的意图分析置信度很低。
因此，本次回复的核心任务是 **澄清和确认**。
请使用一种温和、不冒犯的方式，尝试询问用户的真实意图，而不是直接回答。
例如，你可以说：“我不太确定你是不是指...呢？” 或 “能再多告诉我一些细节吗？”
同时，请严格保持你的人设。
"""
        else:
            final_strategy_prompt = f"""
# 用户状态情报 (请仔细阅读)
- 用户主要意图: {intent_analysis_result.primary_intent}
- 用户情绪状态: {intent_analysis_result.emotional_state} (强度: {intent_analysis_result.emotional_intensity}/10)
- 用户深层需求: {intent_analysis_result.underlying_need}
- 用户当前最希望的沟通方式: {intent_analysis_result.user_receptivity}
- 给你的提示: {intent_analysis_result.persona_hint or "无"}
- 建议的回复开头: {intent_analysis_result.reply_seed or "无"}

# 行动策略
你的核心任务是：在严格保持你 `{companion.name}` 人设的同时，
根据上述情报，以最恰当的方式回应用户。
你需要巧妙地满足用户的深层需求，并采用最适合他当前接受度的沟通方式。
"""

        # --- ↓↓↓ 这是关键的修正：移除了 await 关键字 ↓↓↓ ---
        retrieved_knowledge = rag_service.retrieve(query=user_message, companion_id=self.companion_id)
        # --- ↑↑↑ 修正完成 ↑↑↑ ---
        knowledge_context = "\n\n".join(retrieved_knowledge)

        system_prompt_template = f"""
# 你的身份
你是AI伙伴 `{companion.name}`。
你的核心人设与指令如下：
---
{companion.instructions}
---
# 你的对话示例如下
---
{companion.seed}
---
{final_strategy_prompt}
"""
        if knowledge_context:
            system_prompt_template = f"""
# 参考知识 (请优先根据此知识回答)
---
{knowledge_context}
---

{system_prompt_template}
"""
        llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.DEEPSEEK_API_BASE,
            model_name="deepseek-chat",
            temperature=0.7,
            streaming=True,
        )

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt_template),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}"),
        ])

        llm_chain = LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=True)

        await crud_message.create_message(
            self.db, MessageCreate(content=user_message, role="user", companion_id=self.companion_id), self.user_id
        )

        ai_full_response = ""
        async for response_chunk in llm_chain.astream({"input": user_message}):
            content = response_chunk.get("text", "")
            ai_full_response += content
            yield content

        if ai_full_response:
            await crud_message.create_message(
                self.db, MessageCreate(content=ai_full_response, role="ai", companion_id=self.companion_id), self.user_id
            )
            await self.memory_manager.save_memory(llm_chain.memory)