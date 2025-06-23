from langchain_openai import AzureChatOpenAI, ChatOpenAI
from app.config import settings
from typing import Any, Optional
import traceback

def get_llm(model_provider=None, model_name=None) -> Any:
    """
    获取LLM实例，支持OpenAI和Ollama
    
    Args:
        model_provider: 模型提供商，可选 'openai' 或 'ollama'
        model_name: 模型名称
        
    Returns:
        语言模型实例
    """
    # 如果未指定，使用配置中的默认值
    model_provider = model_provider or settings.model_provider
    model_name = model_name or settings.model_name
    
    print(f"使用模型提供商: {model_provider}")
    print(f"使用模型: {model_name}")
    
    # 根据提供商选择模型
    if model_provider == "openai":
        # 获取Azure OpenAI配置
        api_key = settings.openai_api_key
        api_version = settings.api_version
        azure_endpoint = settings.azure_endpoint
        
        # 输出配置信息
        print(f"使用Azure OpenAI - Endpoint: {azure_endpoint}")
        print(f"API Version: {api_version}")
        
        # 使用Azure ChatOpenAI创建LLM实例
        llm = AzureChatOpenAI(
            model_name=model_name, 
            temperature=0,
            openai_api_key=api_key,
            azure_endpoint=azure_endpoint,
            openai_api_version=api_version
        )
    
    elif model_provider == "ollama":
        try:
            # 仅在需要时导入Ollama
            from langchain_community.llms import Ollama
            
            # 使用Ollama本地模型
            ollama_base_url = settings.ollama_base_url
            print(f"使用Ollama - Base URL: {ollama_base_url}")
            
            # 尝试创建Ollama实例
            try:
                llm = Ollama(
                    model=model_name,
                    base_url=ollama_base_url,
                    temperature=0
                )
                # 测试Ollama是否可用
                llm.invoke("测试")
            except Exception as e:
                print(f"Ollama服务不可用: {str(e)}")
                print(f"详细错误: {traceback.format_exc()}")
                print("回退到OpenAI模型")
                
                # 回退到OpenAI
                api_key = settings.openai_api_key
                api_version = settings.api_version
                azure_endpoint = settings.azure_endpoint
                
                llm = AzureChatOpenAI(
                    model_name=settings.model_name, 
                    temperature=0,
                    openai_api_key=api_key,
                    azure_endpoint=azure_endpoint,
                    openai_api_version=api_version
                )
        except ImportError:
            print("Ollama库未安装，回退到OpenAI模型")
            
            # 回退到OpenAI
            api_key = settings.openai_api_key
            api_version = settings.api_version
            azure_endpoint = settings.azure_endpoint
            
            llm = AzureChatOpenAI(
                model_name=settings.model_name, 
                temperature=0,
                openai_api_key=api_key,
                azure_endpoint=azure_endpoint,
                openai_api_version=api_version
            )
    
    else:
        raise ValueError(f"不支持的模型提供商: {model_provider}")
    
    return llm 