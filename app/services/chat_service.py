from uuid import UUID
import asyncio
from sqlalchemy.orm import Session
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

class ChatService:
    def __init__(self, db: Session, redis_client: redis.Redis, companion: Companion, user_id: UUID):
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
        # 1. 延迟导入和初始化 LangChain 相关组件
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.DEEPSEEK_API_BASE,
            model_name="deepseek-chat",
            temperature=0.7,
            streaming=True,
        )

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                f"""
                {self.companion.instructions}
                Here is an example of how you should talk:
                {self.companion.seed}
                """
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}"),
        ])

        # 异步获取记忆
        memory = await self.memory_manager.get_memory()
        
        llm_chain = LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=True)

        # 2. 安全地在异步环境中执行同步的数据库操作
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, 
            crud_message.create_message, 
            self.db, 
            MessageCreate(content=user_message, role="user", companion_id=self.companion.id),
            self.user_id
        )
        
        # 3. 流式获取响应
        ai_full_response = ""
        async for response_chunk in llm_chain.astream({"input": user_message}):
            content = response_chunk.get("text", "")
            ai_full_response += content
            yield content
        
        # 4. 安全地保存 AI 回复和记忆
        if ai_full_response:
            await loop.run_in_executor(
                None,
                crud_message.create_message,
                self.db,
                MessageCreate(content=ai_full_response, role="ai", companion_id=self.companion.id),
                self.user_id
            )
            await self.memory_manager.save_memory(llm_chain.memory)
