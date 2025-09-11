from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from langchain.chains import LLMChain
from langchain.prompts import (
    ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
)
from typing import AsyncGenerator

from app.core.config import settings
from app.models.companion import Companion
from app.services.memory_manager import MemoryManager
from app.crud import crud_message
from app.schemas.message import MessageCreate
import redis.asyncio as redis
from app.services.rag_service import rag_service

class ChatService:
    def __init__(self, db: AsyncSession, redis_client: redis.Redis, companion: Companion, user_id: UUID):
        self.db = db
        self.redis_client = redis_client
        self.companion = companion
        self.user_id = user_id
        self.memory_manager = MemoryManager(
            redis_client=self.redis_client,
            companion_name=self.companion.name, 
            user_id=str(self.user_id),
            ai_prefix=self.companion.name,
        )

    async def process_user_message(self, user_message: str) -> AsyncGenerator[str, None]:
        """处理用户消息，并以流的形式返回 AI 回复。"""

        # --- 【【【关键修复：在这里提前获取 ID】】】 ---
        # 在进入 LangChain stream 之前，从 companion 对象中安全地获取 ID。
        companion_id = self.companion.id
        # --- 修复结束 ---
        
        retrieved_knowledge = rag_service.retrieve(
            query=user_message,
            companion_id=companion_id # 使用本地变量
        )
        knowledge_context = "\n\n".join(retrieved_knowledge)
        
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.DEEPSEEK_API_BASE,
            model_name="deepseek-chat",
            temperature=0.7,
            streaming=True,
        )

        base_prompt_template = f"""
        {self.companion.instructions}
        Here is an example of how you should talk:
        {self.companion.seed}
        """

        if knowledge_context:
            augmented_prompt_template = f"""
            Answer the user's question based ONLY on the following background knowledge. If the answer is not in the knowledge, say you don't know.
            ---BACKGROUND KNOWLEDGE---
            {knowledge_context}
            ---END BACKGROUND KNOWLEDGE---
            Your core instructions are:
            {base_prompt_template}
            """
            system_prompt = SystemMessagePromptTemplate.from_template(augmented_prompt_template)
        else:
            system_prompt = SystemMessagePromptTemplate.from_template(base_prompt_template)
        
        prompt = ChatPromptTemplate.from_messages([
            system_prompt,
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}"),
        ])

        memory = await self.memory_manager.get_memory()
        
        llm_chain = LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=True)

        # 1. 保存用户消息 (在 stream 之前，这里是安全的)
        await crud_message.create_message(
            self.db, 
            MessageCreate(content=user_message, role="user", companion_id=companion_id),
            self.user_id
        )
        
        # 2. 运行 AI stream
        ai_full_response = ""
        async for response_chunk in llm_chain.astream({"input": user_message}):
            content = response_chunk.get("text", "")
            ai_full_response += content
            yield content
        
        # 3. 保存 AI 消息
        if ai_full_response:
            await crud_message.create_message(
                self.db,
                # 【【【关键修复：使用我们之前保存的 companion_id 变量】】】
                MessageCreate(content=ai_full_response, role="ai", companion_id=companion_id),
                self.user_id
            )
            await self.memory_manager.save_memory(llm_chain.memory)