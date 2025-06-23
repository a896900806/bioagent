from fastapi import FastAPI, HTTPException
from app.config import settings
import sqlite3
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal
from app.graph.builder import invoke_graph
from app.graph.memory import memory_saver
import traceback
import uuid

app = FastAPI()

@app.get("/healthz")
def healthz():
    print("OpenAI Key Prefix:", settings.openai_api_key[:4])
    return {"status": "ok"}

class GSERecord(BaseModel):
    id: int
    accession: str
    title: str

@app.get("/api/gse", response_model=List[GSERecord])
def get_gse_records():
    """获取所有GSE记录"""
    conn = sqlite3.connect(settings.database_url.split("///")[-1])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gse")
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

@app.get("/api/gse/{accession}", response_model=GSERecord)
def get_gse_by_accession(accession: str):
    """根据登录号获取GSE记录"""
    conn = sqlite3.connect(settings.database_url.split("///")[-1])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gse WHERE accession = ?", (accession,))
    result = dict(cursor.fetchone())
    conn.close()
    return result

class QueryRequest(BaseModel):
    query: str
    model_provider: Optional[Literal["openai", "ollama"]] = None
    model_name: Optional[str] = None
    thread_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    sql_result: Optional[str] = None
    rag_result: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    thread_id: Optional[str] = None
    error: Optional[str] = None

@app.post("/api/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """
    处理生物信息查询
    
    使用LangGraph处理查询，结合SQL和RAG
    可选择不同的模型提供商和模型名称
    支持通过thread_id保持对话上下文
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="查询不能为空")
    
    try:
        # 如果请求了ollama但没有ollama，使用openai
        model_provider = request.model_provider
        if model_provider == "ollama":
            try:
                import langchain_community.llms.ollama
                print("Ollama模块可用，尝试使用Ollama")
            except ImportError:
                print("Ollama模块不可用，自动切换到OpenAI")
                model_provider = "openai"
        
        # 获取或生成thread_id
        thread_id = request.thread_id
        if not thread_id:
            thread_id = str(uuid.uuid4())
            print(f"生成新的会话ID: {thread_id}")
        else:
            print(f"使用现有会话ID: {thread_id}")
        
        # 调用图处理查询，传递模型选择参数和thread_id
        result = invoke_graph(
            request.query, 
            model_provider=model_provider, 
            model_name=request.model_name,
            thread_id=thread_id
        )
        
        # 提取所有结果
        response = {
            "answer": result.get("answer", "无法获取答案"),
            "intent": result.get("intent", "unknown"),
            "sql_result": result.get("sql_answer"),
            "rag_result": result.get("rag_answer"),
            "model_provider": result.get("model_provider"),
            "model_name": result.get("model_name"),
            "thread_id": result.get("thread_id", thread_id),
            "error": None
        }
        
        return response
    except Exception as e:
        error_detail = f"处理查询时出错: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        
        # 返回错误但不中断API
        return {
            "answer": f"处理查询时出错: {str(e)}",
            "intent": "error",
            "sql_result": None,
            "rag_result": None,
            "model_provider": request.model_provider or settings.model_provider,
            "model_name": request.model_name or settings.model_name,
            "thread_id": request.thread_id,
            "error": str(e)
        }

@app.get("/api/threads")
def list_threads():
    """
    列出所有活跃的对话线程
    
    返回当前系统中存在的所有对话线程ID列表
    """
    try:
        # 根据LangGraph文档，list方法需要提供config参数
        config = {}
        threads = memory_saver.list(config)
        return {"threads": threads}
    except Exception as e:
        error_detail = f"获取线程列表出错: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/threads/{thread_id}")
def delete_thread(thread_id: str):
    """
    删除特定对话线程
    
    删除指定ID的对话线程及其所有历史记录
    """
    try:
        # 使用delete_thread方法删除线程
        try:
            memory_saver.delete_thread(thread_id)
            return {"message": "对话线程已删除", "thread_id": thread_id}
        except KeyError:
            raise HTTPException(status_code=404, detail="对话线程不存在")
    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"删除线程出错: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/threads")
def clear_all_threads():
    """
    清空所有对话线程
    
    删除系统中所有的对话线程及其历史记录
    """
    try:
        # 获取所有线程ID
        config = {}
        threads = memory_saver.list(config)
        # 逐个删除线程
        for thread_id in threads:
            memory_saver.delete_thread(thread_id)
        return {"message": "所有对话线程已清空"}
    except Exception as e:
        error_detail = f"清空线程出错: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
def get_available_models():
    """获取可用的模型提供商和模型列表"""
    # 检查Ollama是否可用
    ollama_available = False
    try:
        import langchain_community.llms.ollama
        try:
            # 尝试简单调用
            from langchain_community.llms import Ollama
            Ollama(base_url=settings.ollama_base_url).invoke("test")
            ollama_available = True
        except:
            ollama_available = False
    except ImportError:
        ollama_available = False
    
    return {
        "providers": [
            {
                "name": "openai",
                "models": ["gpt-4o", "gpt-3.5-turbo"],
                "available": True
            },
            {
                "name": "ollama",
                "models": ["llama3", "mistral", "bge-m3"],
                "available": ollama_available
            }
        ],
        "default_provider": settings.model_provider,
        "default_model": settings.model_name
    } 