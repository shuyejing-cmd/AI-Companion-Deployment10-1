# app/services/knowledge_service.py

import logging
import os
from uuid import UUID
from pathlib import Path
from typing import List

# --- 数据库 & CRUD ---
from app.db.session import AsyncSessionLocal
from app.crud import crud_knowledge_file
from app.models.knowledge_file import KnowledgeFile

# --- 文档处理 (LangChain) ---
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# --- 向量化 & 向量数据库 ---
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class KnowledgeService:
    """
    封装了所有与知识库文件处理、向量化和检索相关的业务逻辑。
    """

    def __init__(self):
        # 1. 初始化嵌入模型 (Embedding Model)
        # 在服务实例化时加载模型，避免每次任务都重新加载，提高效率。
        # 'bge-large-zh-v1.5' 是一个优秀的中英双语嵌入模型。
        # 使用 cache_folder 将模型缓存到项目目录下，避免每次 Docker 重启都重新下载。
        model_cache_path = Path("./models_cache")
        model_cache_path.mkdir(exist_ok=True)
        self.embedding_model = SentenceTransformer(
            'BAAI/bge-large-zh-v1.5', 
            cache_folder=str(model_cache_path)
        )
        
        # 2. 初始化 Pinecone 客户端
        self.pinecone = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.pinecone_index_name = "ai-companion-index" # 暂时硬编码，未来可以根据 companion 配置
        
        if self.pinecone_index_name not in self.pinecone.list_indexes().names():
            # 如果索引不存在，这里可以根据需要自动创建，但需要指定维度
            # 目前的策略是要求索引必须预先存在
            raise ValueError(f"Pinecone index '{self.pinecone_index_name}' does not exist.")
        self.pinecone_index = self.pinecone.Index(self.pinecone_index_name)

    async def process_and_index_file(self, file_id: UUID):
        """
        核心方法：处理单个文件并将其向量化存入 Pinecone。
        这是 ARQ worker 将要调用的主要任务。
        """
        # 为每个任务创建一个独立的数据库会话，这是后台任务的最佳实践
        async with AsyncSessionLocal() as db:
            try:
                # 1. 获取文件记录并更新状态为 PROCESSING
                db_file = await crud_knowledge_file.update_status(
                    db, file_id=file_id, status="PROCESSING"
                )
                if not db_file:
                    logging.error(f"File with id {file_id} not found in database.")
                    return

                logging.info(f"开始处理文件: {db_file.file_path}")

                # 2. 加载文档内容
                documents = self._load_documents(db_file.file_path)
                if not documents:
                    raise ValueError("Failed to load any content from the document.")

                # 3. 分割文档成文本块 (Chunks)
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,   # 每个块的最大字符数
                    chunk_overlap=200, # 相邻块之间的重叠字符数
                )
                chunks = text_splitter.split_documents(documents)
                logging.info(f"文件被分割成 {len(chunks)} 个文本块 (chunks)")
                if not chunks:
                    raise ValueError("Document is empty or could not be split into chunks.")

                # 4. 向量化文本块并分批上传到 Pinecone
                await self._embed_and_upsert_chunks(
                    chunks=chunks,
                    companion_id=db_file.companion_id,
                    file_id=db_file.id,
                    file_name=db_file.file_name,
                )
                
                # 5. 全部成功后，更新数据库状态为 INDEXED
                await crud_knowledge_file.update_status(
                    db, file_id=file_id, status="INDEXED"
                )
                logging.info(f"文件 {db_file.file_name} (id: {file_id}) 处理并索引成功!")

            except Exception as e:
                logging.error(f"处理文件 {file_id} 时发生严重错误: {e}", exc_info=True)
                # 如果发生任何错误，更新状态为 FAILED 并记录详细错误信息
                await crud_knowledge_file.update_status(
                    db,
                    file_id=file_id,
                    status="FAILED",
                    error_message=f"{type(e).__name__}: {e}",
                )

    def _load_documents(self, file_path_str: str) -> List[Document]:
        """根据文件扩展名选择合适的加载器来加载文档"""
        file_path = Path(file_path_str)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found at path: {file_path}")

        ext = file_path.suffix.lower()
        if ext == ".txt":
            loader = TextLoader(str(file_path), encoding="utf-8")
        elif ext == ".md":
            loader = UnstructuredMarkdownLoader(str(file_path))
        elif ext == ".pdf":
            loader = PyPDFLoader(str(file_path))
        else:
            raise ValueError(f"Unsupported file type for RAG: {ext}")
        
        return loader.load()

    async def _embed_and_upsert_chunks(
        self, chunks: List[Document], companion_id: UUID, file_id: UUID, file_name: str
    ):
        """将文本块向量化并分批上传到 Pinecone"""
        batch_size = 100  # Pinecone 推荐的批处理大小
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            
            # 提取批次的文本内容
            texts = [chunk.page_content for chunk in batch_chunks]
            
            # 向量化
            logging.info(f"正在为 {len(texts)} 个文本块生成向量 (Batch {i//batch_size + 1})...")
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # 准备上传到 Pinecone 的数据结构
            vectors_to_upsert = []
            for j, chunk in enumerate(batch_chunks):
                # 为每个 chunk 创建一个唯一的、可追溯的 ID
                vector_id = f"{file_id}_{i+j}" 
                metadata = {
                    "text": chunk.page_content,
                    "companion_id": str(companion_id),
                    "file_id": str(file_id),
                    "file_name": file_name,
                }
                vectors_to_upsert.append({
                    "id": vector_id,
                    "values": embeddings[j],
                    "metadata": metadata,
                })
            
            # 上传到 Pinecone
            logging.info(f"正在上传 {len(vectors_to_upsert)} 个向量到 Pinecone...")
            self.pinecone_index.upsert(vectors=vectors_to_upsert)