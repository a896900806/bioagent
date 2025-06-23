from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from app.data_loader.load_docs import load_documents
from app.config import settings
import os
from tqdm import tqdm

def ingest_docs():
    """
    加载文档，创建嵌入，并保存到Chroma向量数据库
    """
    print("加载文档...")
    docs = load_documents()
    
    print(f"加载了 {len(docs)} 个文档")
    
    print("创建嵌入...")
    # 使用本地Ollama模型创建嵌入
    try:
        embeddings = OllamaEmbeddings(model="bge-m3")
        print("成功初始化Ollama嵌入模型")
    except Exception as e:
        print(f"初始化Ollama嵌入模型失败: {str(e)}")
        print("使用备用嵌入方法...")
        
        # 使用备用嵌入方法（简单的零向量）
        class DummyEmbeddings:
            def embed_documents(self, texts):
                """返回固定维度的零向量"""
                return [[0.0] * 384 for _ in texts]
                
            def embed_query(self, text):
                """返回固定维度的零向量"""
                return [0.0] * 384
        
        embeddings = DummyEmbeddings()
        print("使用备用嵌入方法（仅用于测试）")
    
    # 确保向量数据库目录存在
    vector_db_path = os.path.join(os.getcwd(), "data", "chroma")
    os.makedirs(vector_db_path, exist_ok=True)
    
    print(f"创建向量数据库并保存到 {vector_db_path}...")
    db = Chroma.from_documents(
        documents=docs,
        collection_name="bio-rag",
        embedding=embeddings,
        persist_directory=vector_db_path
    )
    
    # 持久化存储
    db.persist()
    
    print("向量数据库创建完成!")
    return db

if __name__ == "__main__":
    ingest_docs() 