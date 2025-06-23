from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.tools.llm_toolkit import get_llm
import os
import traceback

# 创建内存向量存储作为后备
class MemoryVectorStore:
    def similarity_search(self, query, k=4):
        """
        内存向量存储的相似性搜索
        
        Args:
            query: 查询字符串
            k: 返回的文档数量
            
        Returns:
            文档列表
        """
        return [
            Document(page_content="这是一个内存向量存储的示例文档。由于无法访问真实的向量数据库，我们返回这个占位符。"),
            Document(page_content="生物信息数据分析通常涉及基因组、转录组和蛋白质组等多种组学数据。"),
            Document(page_content="GSE数据库是NCBI的基因表达综合数据库，收集了大量基因表达实验数据。"),
            Document(page_content="生物信息学结合了生物学、计算机科学和统计学方法，用于分析大规模生物数据。"),
            Document(page_content="GSE10000是一个关于小鼠肝脏表达的数据集，包含了多个样本的基因表达数据。"),
            Document(page_content="GSE20000是一个人类大脑单细胞测序数据集，用于研究脑细胞的异质性。")
        ]

# 创建空的嵌入函数作为后备
class DummyEmbeddings:
    def embed_documents(self, texts):
        """返回固定维度的零向量"""
        return [[0.0] * 384 for _ in texts]
        
    def embed_query(self, text):
        """返回固定维度的零向量"""
        return [0.0] * 384

# RAG提示模板
RAG_TEMPLATE = """基于以下上下文信息，回答问题。如果上下文中没有相关信息，请说明无法回答。

上下文信息:
{context}

问题: {query}

回答:"""

# 直接使用内存向量存储，跳过Ollama嵌入
print("使用内存向量存储进行RAG检索")
vectordb = MemoryVectorStore()

# 以下代码暂时注释掉，因为没有Ollama服务
"""
try:
    # 设置向量数据库路径
    vector_db_path = settings.vector_db_path
    if vector_db_path.startswith("./") or vector_db_path.startswith("../"):
        vector_db_path = os.path.normpath(os.path.join(os.getcwd(), vector_db_path))
    
    # 创建数据目录
    try:
        os.makedirs(vector_db_path, exist_ok=True)
        print(f"向量数据库路径: {vector_db_path}")
    except Exception as e:
        print(f"无法创建向量数据库目录: {str(e)}")
        vector_db_path = os.path.join(os.getcwd(), "temp_vector_db")
        os.makedirs(vector_db_path, exist_ok=True)
        print(f"使用临时向量数据库路径: {vector_db_path}")
        
    # 创建嵌入模型
    try:
        # 尝试使用Ollama嵌入
        from langchain_ollama import OllamaEmbeddings
        embeddings = OllamaEmbeddings(model="bge-m3")
        print("成功初始化Ollama嵌入模型")
    except Exception as e:
        print(f"初始化Ollama嵌入模型失败: {str(e)}")
        print("使用虚拟嵌入模型")
        embeddings = DummyEmbeddings()
        
    # 创建或加载向量数据库
    try:
        vectordb = Chroma(
            collection_name="bio-rag",
            embedding_function=embeddings,
            persist_directory=vector_db_path
        )
        print(f"成功加载向量数据库: {vector_db_path}")
        
        # 检查是否为空，如果为空则添加一些示例文档
        if vectordb._collection.count() == 0:
            print("向量数据库为空，添加示例文档")
            sample_texts = [
                "生物信息学是一个将生物学、计算机科学和统计学结合的交叉学科领域。",
                "基因表达数据分析通常包括质量控制、标准化和差异表达分析等步骤。",
                "单细胞RNA测序(scRNA-seq)技术能够揭示细胞间的异质性。",
                "GSE数据库是NCBI的基因表达综合数据库，收集了大量基因表达实验数据。",
                "GSE10000是一个关于小鼠肝脏表达的数据集，包含了多个样本的基因表达数据。",
                "GSE20000是一个人类大脑单细胞测序数据集，用于研究脑细胞的异质性。"
            ]
            vectordb.add_texts(sample_texts)
            print("添加了6个示例文档到向量数据库")
    except Exception as e:
        print(f"加载向量数据库失败: {str(e)}")
        print(f"详细错误: {traceback.format_exc()}")
        print("使用内存向量存储")
        vectordb = MemoryVectorStore()
except Exception as e:
    print(f"向量数据库初始化失败: {str(e)}")
    print(f"详细错误: {traceback.format_exc()}")
    print("使用内存向量存储")
    vectordb = MemoryVectorStore()
"""

def get_rag_chain(llm=None):
    """
    创建一个简单的RAG查询链
    
    Args:
        llm: 语言模型实例，如果未提供则使用默认模型
        
    Returns:
        一个可以执行RAG查询的链
    """
    # 如果未提供LLM，则使用默认配置创建一个
    if llm is None:
        try:
            llm = get_llm()
        except Exception as e:
            print(f"获取默认LLM失败: {str(e)}")
            # 创建一个简单的虚拟LLM作为后备
            class DummyLLM:
                def invoke(self, prompt):
                    class DummyResponse:
                        content = "无法获取语言模型实例，返回占位符回答。"
                    return DummyResponse()
            llm = DummyLLM()
    
    # 创建提示模板
    prompt = PromptTemplate.from_template(RAG_TEMPLATE)
    
    # 返回一个简单的包装对象，提供run方法
    class RAGChain:
        def run(self, query):
            try:
                # 执行向量检索
                docs = vectordb.similarity_search(query, k=4)
                context = "\n\n".join([doc.page_content for doc in docs])
                
                if isinstance(vectordb, MemoryVectorStore):
                    context += "\n\n注意：这是一个内存向量存储的占位符，包含了一些基本的生物信息学信息。"
                
                # 填充提示模板
                formatted_prompt = prompt.format(context=context, query=query)
                
                # 使用LLM生成回答
                try:
                    response = llm.invoke(formatted_prompt)
                    return response.content
                except Exception as e:
                    print(f"生成回答时出错: {str(e)}")
                    print(f"详细错误: {traceback.format_exc()}")
                    return f"生成回答时出错: {str(e)}"
            except Exception as e:
                print(f"检索错误: {str(e)}")
                print(f"详细错误: {traceback.format_exc()}")
                return f"检索错误: {str(e)}"
    
    return RAGChain() 