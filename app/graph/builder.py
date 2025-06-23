from typing import Dict, Any, TypedDict, Optional, Annotated, Literal, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from app.graph.nodes import sql_node, rag_node, aggregator_node, intent_classifier_node, route_node, chat_node
from app.tools.llm_toolkit import get_llm
from app.config import settings
import os
import uuid
from app.graph.memory import memory_saver

# 定义消息类型
class Message(TypedDict):
    role: str
    content: str

# 定义状态类型
class AgentState(TypedDict):
    query: str
    llm: Any
    intent: Optional[str]
    sql_answer: Optional[str]
    rag_answer: Optional[str]
    answer: Optional[str]
    model_provider: Optional[str]
    model_name: Optional[str]
    thread_id: Optional[str]
    messages: Optional[List[Message]]

def build_graph() -> StateGraph:
    """
    构建LangGraph处理图
    
    Returns:
        StateGraph: 编译后的图
    """
    # 创建图的状态定义
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("sql", sql_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("chat", chat_node)
    workflow.add_node("aggregator", aggregator_node)
    
    # 定义图的流程
    # 从意图分类器节点开始
    workflow.set_entry_point("intent_classifier")
    
    # 定义节点间的连接
    
    # 根据意图分类结果路由到不同节点
    workflow.add_conditional_edges(
        "intent_classifier",
        # 这个函数决定下一步去哪个节点
        lambda state: state["intent"],
        {
            "sql": "sql",         # 如果意图是SQL，则去SQL节点
            "rag": "rag",         # 如果意图是RAG，则去RAG节点
            "both": "sql",        # 如果意图是BOTH，先去SQL节点
            "unknown": "rag",     # 如果意图未知，默认去RAG节点
            "chat": "chat"        # 如果意图是普通聊天，则去聊天节点
        }
    )
    
    # SQL节点后根据意图决定下一步
    workflow.add_conditional_edges(
        "sql",
        # 这个函数决定SQL节点后去哪里
        lambda state: "rag" if state["intent"] in ["both", "unknown"] else "aggregator",
        {
            "rag": "rag",              # 如果需要两者，则继续到RAG节点
            "aggregator": "aggregator" # 如果只需要SQL，则直接去聚合器
        }
    )
    
    # RAG节点后永远去聚合器
    workflow.add_edge("rag", "aggregator")
    
    # 聊天节点后不需要其他处理，直接结束
    workflow.add_edge("chat", END)
    
    # 设置聚合器为最终节点
    workflow.set_finish_point("aggregator")
    
    # 编译图，使用内存存储提供短期记忆功能
    return workflow.compile(checkpointer=memory_saver)

def invoke_graph(query: str, model_provider=None, model_name=None, thread_id=None) -> Dict[str, Any]:
    """
    调用图处理查询
    
    Args:
        query: 用户查询
        model_provider: 模型提供商，可选 'openai' 或 'ollama'
        model_name: 模型名称
        thread_id: 对话线程ID，用于保持对话上下文
        
    Returns:
        Dict: 包含处理结果的字典
    """
    # 如果未提供thread_id，生成一个新的
    if thread_id is None:
        thread_id = str(uuid.uuid4())
        print(f"生成新的对话线程ID: {thread_id}")
    
    # 构建图
    graph = build_graph()
    
    # 获取LLM实例
    llm = get_llm(model_provider, model_name)
    
    # 设置初始输入
    inputs = {
        "query": query,
        "llm": llm,
        "model_provider": model_provider or settings.model_provider,
        "model_name": model_name or settings.model_name,
        "thread_id": thread_id  # 将thread_id直接添加到初始状态中
    }
    
    # 执行图，添加错误处理
    try:
        print(f"执行查询: {query}")
        print(f"对话线程ID: {thread_id}")
        
        # 根据LangGraph文档，正确的方式是在configurable中传递thread_id
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(inputs, config)
        
        # 将thread_id添加到结果中
        result["thread_id"] = thread_id
        
        # 确保返回一个有效的回答
        if not result.get("answer"):
            return {
                "answer": "无法处理查询，请尝试其他问题。",
                "thread_id": thread_id
            }
        
        return result
    except Exception as e:
        print(f"图执行错误: {e}")
        return {
            "answer": f"处理查询时出错: {str(e)}",
            "thread_id": thread_id
        } 