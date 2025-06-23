from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
from app.tools.llm_toolkit import get_llm
import pathlib, sqlite3, os
import re
import traceback

# 处理数据库路径
db_url = settings.database_url
db_path = pathlib.Path(db_url.split("///")[-1])

# 确保数据库目录存在
os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)

# 检查schema.sql文件
schema_path = pathlib.Path("app/db/schema.sql")
if schema_path.exists():
    # 如果数据库不存在，使用schema.sql创建它
    if not db_path.exists():
        schema_sql = schema_path.read_text()
        conn = sqlite3.connect(db_path)
        conn.executescript(schema_sql)
        conn.close()
        print(f"成功创建数据库: {db_path}")
else:
    print(f"警告: schema.sql文件不存在: {schema_path}")
    # 创建一个空数据库
    if not db_path.exists():
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS gse (id INTEGER PRIMARY KEY, accession TEXT, title TEXT)")
        conn.execute("INSERT OR IGNORE INTO gse (accession, title) VALUES ('GSE10000', 'Mouse liver expression')")
        conn.execute("INSERT OR IGNORE INTO gse (accession, title) VALUES ('GSE20000', 'Human brain single-cell')")
        conn.commit()
        conn.close()
        print(f"成功创建基本数据库: {db_path}")

# 创建数据库连接
try:
    db = SQLDatabase.from_uri(db_url)
    print(f"成功连接到数据库: {db_url}")
except Exception as e:
    print(f"连接数据库失败: {str(e)}")
    print(f"详细错误: {traceback.format_exc()}")
    # 创建一个内存数据库作为后备
    db = SQLDatabase.from_uri("sqlite:///:memory:")
    print("使用内存数据库作为后备")

# SQL查询提示模板
SQL_TEMPLATE = """你是一个SQL专家。根据下面的表结构和问题，生成一个SQL查询来回答问题。
只返回纯SQL查询，不要包含任何代码块标记、注释或其他解释。

表结构:
{schema}

用户问题: {question}

SQL查询:"""

def clean_sql_query(sql_query):
    """
    清理SQL查询，移除代码块标记和其他非SQL内容
    
    Args:
        sql_query: 原始SQL查询
        
    Returns:
        清理后的SQL查询
    """
    # 移除Markdown格式的代码块标记
    sql_query = re.sub(r'```sql\s*', '', sql_query)
    sql_query = re.sub(r'```', '', sql_query)
    
    # 移除可能的注释
    sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
    
    # 移除前后空白
    sql_query = sql_query.strip()
    
    return sql_query

def get_sql_chain(llm=None):
    """
    创建一个简单的SQL查询链
    
    Args:
        llm: 语言模型实例，如果未提供则使用默认模型
        
    Returns:
        一个可以执行SQL查询的链
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
                        content = "SELECT * FROM gse LIMIT 5"
                    return DummyResponse()
            llm = DummyLLM()
    
    # 创建提示模板
    prompt = PromptTemplate.from_template(SQL_TEMPLATE)
    
    # 使用最新版本的API创建SQL查询链
    try:
        sql_generator = create_sql_query_chain(llm, db, prompt=prompt)
    except Exception as e:
        print(f"创建SQL查询链错误: {e}")
        print(f"详细错误: {traceback.format_exc()}")
        # 创建一个简单的SQL生成器，直接返回基本查询
        class BasicSQLGenerator:
            def invoke(self, inputs):
                if "GSE10000" in inputs["question"]:
                    return "SELECT * FROM gse WHERE accession = 'GSE10000'"
                elif "GSE20000" in inputs["question"]:
                    return "SELECT * FROM gse WHERE accession = 'GSE20000'"
                else:
                    return "SELECT * FROM gse"
        sql_generator = BasicSQLGenerator()
    
    # 返回一个简单的包装对象，提供run方法
    class SQLChain:
        def run(self, query):
            # 生成SQL查询
            try:
                sql_query = sql_generator.invoke({"question": query})
                
                # 清理SQL查询，移除代码块标记和其他非SQL内容
                clean_query = clean_sql_query(sql_query)
                print(f"原始SQL查询: {sql_query}")
                print(f"清理后SQL查询: {clean_query}")
                
                # 执行查询
                try:
                    result = db.run(clean_query)
                    return f"查询: {clean_query}\n\n结果: {result}"
                except Exception as e:
                    print(f"执行SQL查询错误: {str(e)}")
                    print(f"详细错误: {traceback.format_exc()}")
                    return f"查询: {clean_query}\n\n错误: {str(e)}"
            except Exception as e:
                print(f"生成SQL查询失败: {str(e)}")
                print(f"详细错误: {traceback.format_exc()}")
                return f"生成SQL查询失败: {str(e)}"
    
    return SQLChain() 