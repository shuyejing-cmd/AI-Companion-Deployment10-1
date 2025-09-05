# app/services/rag_service.py

import logging
from uuid import UUID
from pathlib import Path
from typing import List

from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class RAGService:
    """
    封装了所有与 RAG 检索相关的业务逻辑。
    """

    def __init__(self):
        # --- 复用 KnowledgeService 中的初始化逻辑，确保一致性 ---
        logging.info("Initializing RAGService...")
        
        # 1. 初始化嵌入模型 (Embedding Model)
        # SentenceTransformer 会自动处理模型的下载和缓存。
        model_cache_path = Path("./models_cache")
        model_cache_path.mkdir(exist_ok=True)
        logging.info("Loading embedding model BAAI/bge-large-zh-v1.5...")
        self.embedding_model = SentenceTransformer(
            'BAAI/bge-large-zh-v1.5', 
            cache_folder=str(model_cache_path)
        )
        
        # 2. 初始化 Pinecone 客户端
        logging.info("Initializing Pinecone client...")
        self.pinecone = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.pinecone_index_name = "ai-companion-index" # 与 KnowledgeService 保持一致
        
        if self.pinecone_index_name not in self.pinecone.list_indexes().names():
            raise ValueError(f"Pinecone index '{self.pinecone_index_name}' does not exist.")
        self.pinecone_index = self.pinecone.Index(self.pinecone_index_name)
        logging.info("RAGService initialized successfully.")

    def retrieve(self, query: str, companion_id: UUID, top_k: int = 3) -> List[str]:
        """
        根据用户问题和伙伴ID，从 Pinecone 检索相关的知识文本块。
        
        :param query: 用户的提问字符串。
        :param companion_id: 正在对话的伙伴的 UUID。
        :param top_k: 希望检索回的最相关文本块的数量。
        :return: 一个包含相关知识文本的字符串列表。
        """
        logging.info(f"Retrieving knowledge for companion '{companion_id}' with query: '{query}'")

        # 1. 将用户问题向量化
        query_vector = self.embedding_model.encode(query).tolist()

        # 2. 使用元数据过滤器，确保只检索属于特定 companion 的知识
        #    这是实现多租户数据隔离的关键
        metadata_filter = {"companion_id": {"$eq": str(companion_id)}}

        # 3. 执行 Pinecone 查询
        try:
            results = self.pinecone_index.query(
                vector=query_vector,
                filter=metadata_filter,
                top_k=top_k,
                include_metadata=True
            )
        except Exception as e:
            logging.error(f"Pinecone query failed for companion '{companion_id}': {e}")
            return [] # 查询失败时返回空列表，保证程序的健壮性

        # 4. 提取并返回检索到的文本内容
        retrieved_texts = [match['metadata']['text'] for match in results.get('matches', [])]
        logging.info(f"Retrieved {len(retrieved_texts)} text chunks from Pinecone.")
        
        return retrieved_texts

# --- 单例模式 ---
# 创建一个 RAGService 的全局单例，方便在应用的其他地方复用。
# 这样可以确保昂贵的模型和客户端连接只在应用启动时被初始化一次，
# 从而大大提高后续请求的处理性能。
rag_service = RAGService()