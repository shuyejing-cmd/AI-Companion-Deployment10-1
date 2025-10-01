# download_model.py
from sentence_transformers import SentenceTransformer

# 你要下载的模型名字
model_name = "BAAI/bge-large-zh-v1.5"

print(f"--- Downloading and caching model: {model_name} ---")
# 这行代码会自动下载模型并缓存到默认路径
SentenceTransformer(model_name)
print("--- Model downloaded successfully. ---")