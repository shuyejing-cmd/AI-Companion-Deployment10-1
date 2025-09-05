# app/db/base.py
# 这个文件用于确保所有模型都被导入，从而能被 Alembic 正确发现。

from app.db.base_class import Base
from app.models.user import User
from app.models.companion import Companion
from app.models.message import Message
from app.models.knowledge_file import KnowledgeFile