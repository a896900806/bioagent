from pydantic_settings import BaseSettings
from typing import Literal, Optional

class Settings(BaseSettings):
    openai_api_key: str
    api_version: str
    azure_endpoint: str
    database_url: str
    vector_db_path: str
    
    # 模型配置
    model_provider: Literal["openai", "ollama"] = "openai"
    model_name: str = "gpt-4o"  # 默认使用OpenAI的gpt-4o
    ollama_base_url: Optional[str] = "http://localhost:11434"  # Ollama的默认URL（可选）
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 