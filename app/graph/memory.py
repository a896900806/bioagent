"""
提供图的内存管理功能
"""
from langgraph.checkpoint.memory import InMemorySaver
import inspect

# 创建全局的内存存储器
# 这将在整个应用程序生命周期内保持会话状态
memory_saver = InMemorySaver()

# 打印InMemorySaver对象的属性，用于调试
print("InMemorySaver的属性和方法:")
for attr in dir(memory_saver):
    if not attr.startswith('__'):
        print(f"- {attr}: {type(getattr(memory_saver, attr))}") 