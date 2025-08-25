import pickle
from typing import List
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema.messages import BaseMessage
import redis.asyncio as redis

class MemoryManager:
    def __init__(self, redis_client: redis.Redis, companion_name: str, user_id: str, ai_prefix: str = "AI"):
        self.redis_client = redis_client
        self.companion_name = companion_name
        self.user_id = user_id
        self.ai_prefix = ai_prefix
        self.memory_key = f"chat_history:{self.companion_name}:{self.user_id}"

    async def get_memory(self, k: int = 30) -> ConversationBufferWindowMemory:
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history", k=k, input_key="input", ai_prefix=self.ai_prefix, return_messages=True
        )
        serialized_history = await self.redis_client.get(self.memory_key)
        if serialized_history:
            history: List[BaseMessage] = pickle.loads(serialized_history)
            memory.chat_memory.messages = history
        return memory

    async def save_memory(self, memory: ConversationBufferWindowMemory):
        serialized_history = pickle.dumps(memory.chat_memory.messages)
        await self.redis_client.set(self.memory_key, serialized_history, ex=60 * 60 * 24 * 7)