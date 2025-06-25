# LangGraph nodes placeholder
# 将用于定义图中的各个节点和处理函数 

import langgraph
from app.tools.sql_toolkit import get_sql_chain
from app.tools.rag_toolkit import get_rag_chain
from typing import Dict, Any, TypedDict, Optional, Annotated, Literal, List
from langgraph.graph import END
from app.graph.memory import memory_saver
import json

# 避免使用复杂的LLMChain对象作为状态
# 而是在每个节点内部创建链

# 定义查询意图类型
QueryIntent = Literal["sql", "rag", "both", "unknown", "chat"]

def intent_classifier_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    意图分类器节点：判断用户查询的意图
    
    Args:
        state: 当前状态，包含查询和LLM实例
        
    Returns:
        更新后的状态，包含意图分类结果
    """
    query = state["query"]
    llm = state["llm"]
    
    # 构建意图分类提示
    intent_prompt = f"""分析以下中文查询，并确定其最适合由哪种系统处理。
    
查询: "{query}"

可能的分类:
- SQL: 如果查询明确请求数据库中的结构化数据，如GSE记录、特定ID、样本数量等。例如"GSE10000包含多少个样本"、"列出所有GSE记录"等。
- RAG: 如果查询寻求一般知识、解释或分析，这些信息可能存在于知识库中。例如"什么是RNA-seq技术"、"解释单细胞测序"等。
- BOTH: 如果查询同时需要结构化数据和知识库信息。例如"GSE10000研究了什么，使用了什么平台"等。
- CHAT: 如果查询与生物信息无关，是普通聊天、日常问题或闲聊。例如"你好"、"今天天气如何"等。
- UNKNOWN: 如果无法确定查询意图。

注意：对于知识性问题（如"什么是..."、"解释..."、"描述..."），通常应该分类为RAG。
对于具体数据查询（如"有多少..."、"列出..."、"获取..."），通常应该分类为SQL。

仅返回一个单词作为分类结果: SQL, RAG, BOTH, CHAT 或 UNKNOWN
"""
    
    try:
        # 使用LLM进行意图分类
        response = llm.invoke(intent_prompt)
        intent = response.content.strip().upper()
        
        # 标准化意图结果
        if "SQL" in intent:
            intent = "sql"
        elif "RAG" in intent:
            intent = "rag"
        elif "BOTH" in intent:
            intent = "both"
        elif "CHAT" in intent:
            intent = "chat"
        else:
            intent = "unknown"
            
        print(f"查询意图分类: {intent}")
        
        # 返回更新后的状态，包含意图
        return {"intent": intent}
    except Exception as e:
        print(f"意图分类错误: {e}")
        # 默认为rag，避免总是使用SQL
        return {"intent": "rag"}

def sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    SQL节点：使用SQL工具包查询数据库
    
    Args:
        state: 当前状态，包含查询和LLM实例
        
    Returns:
        更新后的状态，包含SQL查询结果
    """
    query = state["query"]
    llm = state["llm"]
    
    try:
        # 创建SQL链并执行查询
        sql_chain = get_sql_chain(llm)
        sql_answer = sql_chain.run(query)
        
        # 返回更新后的状态
        return {"sql_answer": sql_answer}
    except Exception as e:
        print(f"SQL查询错误: {e}")
        return {"sql_answer": f"SQL查询错误: {str(e)}"}

def rag_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    RAG节点：使用检索增强生成查询文档
    
    Args:
        state: 当前状态，包含查询和LLM实例
        
    Returns:
        更新后的状态，包含RAG查询结果
    """
    query = state["query"]
    llm = state["llm"]
    
    try:
        # 创建RAG链并执行查询
        rag_chain = get_rag_chain(llm)
        rag_answer = rag_chain.run(query)
        
        # 返回更新后的状态
        return {"rag_answer": rag_answer}
    except Exception as e:
        print(f"RAG查询错误: {e}")
        return {"rag_answer": f"RAG查询错误: {str(e)}"}

def chat_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    聊天节点：处理与生物信息无关的普通聊天
    
    Args:
        state: 当前状态，包含查询和LLM实例
        
    Returns:
        更新后的状态，包含聊天回复
    """
    query = state["query"]
    llm = state["llm"]
    thread_id = state.get("thread_id", "")
    
    # 如果状态中已存在消息历史，则使用它；否则初始化一个新的
    messages = state.get("messages", [])
    
    # 添加当前用户消息到历史
    if not any(msg.get("role") == "user" and msg.get("content") == query for msg in messages):
        messages.append({"role": "user", "content": query})
    
    try:
        print(f"对话线程ID: {thread_id}")
        print(f"历史消息数量: {len(messages)}")
        
        # 聊天系统提示
        system_prompt = """你是一个AI助手，回答用户的各种问题。
对于非生物信息相关的普通聊天，请提供友好、自然、有帮助的回答。
保持回答简洁、清晰。
如果用户询问之前的对话内容，请查看历史消息并进行回答。"""
        
        # 构建完整的聊天请求
        chat_messages = [{"role": "system", "content": system_prompt}]
        chat_messages.extend(messages)
        
        # 打印历史消息用于调试
        print("聊天消息历史:")
        for i, msg in enumerate(chat_messages):
            print(f"  {i}. {msg['role']}: {msg['content'][:50]}...")
        
        # 使用LLM生成回答
        response = llm.invoke(chat_messages)
        chat_answer = response.content.strip()
        
        # 添加AI回复到历史
        messages.append({"role": "assistant", "content": chat_answer})
        
        # 返回更新后的状态
        return {
            "answer": chat_answer,
            "messages": messages  # 保存更新后的消息历史
        }
    except Exception as e:
        print(f"聊天节点错误: {e}")
        return {"answer": f"抱歉，处理您的问题时出现了错误: {str(e)}"}

def aggregator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    聚合器节点：合并SQL和RAG的结果
    
    Args:
        state: 当前状态，包含SQL和RAG的结果
        
    Returns:
        更新后的状态，包含最终合并的答案
    """
    sql = state.get("sql_answer", "")
    rag = state.get("rag_answer", "")
    
    # 合并结果
    if sql and rag:
        answer = f"SQL数据库结果:\n{sql}\n\n知识库检索结果:\n{rag}"
    elif sql:
        answer = f"SQL数据库结果:\n{sql}"
    elif rag:
        answer = f"知识库检索结果:\n{rag}"
    else:
        answer = "未能找到相关信息。"
    
    # 返回最终答案
    return {"answer": answer}

def route_node(state: Dict[str, Any]) -> str:
    """
    路由节点：根据意图决定下一个节点
    
    Args:
        state: 当前状态，包含意图分类结果
        
    Returns:
        下一个节点的名称
    """
    intent = state.get("intent", "rag")
    
    if intent == "sql":
        print("路由到SQL节点")
        return "sql"
    elif intent == "rag":
        print("路由到RAG节点")
        return "rag"
    elif intent == "both":
        print("路由到SQL节点，然后RAG节点")
        return "sql"
    elif intent == "chat":
        print("路由到聊天节点")
        return "chat"
    else:
        print("未知意图，路由到RAG节点作为默认")
        return "rag" 