# BioSearch Agent - 生物信息检索代理系统

BioSearch Agent是一个基于大语言模型的生物信息检索系统，能够同时利用结构化数据库和非结构化知识库来回答生物信息相关查询。系统通过意图识别自动判断查询类型，根据不同需求调用合适的检索模块。

## 功能特点

- **智能意图识别**：自动判断查询是需要结构化数据、知识库信息、两者结合，还是普通聊天
- **SQL数据查询**：从关系型数据库中检索结构化的生物信息数据
- **RAG知识检索**：使用检索增强生成技术从向量数据库中获取相关知识
- **灵活的处理流程**：基于LangGraph构建的动态处理流，根据查询意图自动路由
- **Azure OpenAI集成**：利用Azure OpenAI服务提供高质量的语言理解和生成能力
- **多模型支持**：支持切换OpenAI和Ollama本地模型
- **对话上下文保持**：支持通过线程ID保持多轮对话上下文

## 系统架构

系统由以下核心组件构成：

1. **FastAPI后端**：提供RESTful API接口，接收查询请求并返回结果
2. **LangGraph处理图**：构建动态流程处理图，包含意图分类、查询处理和结果聚合
3. **SQL工具链**：连接和查询SQLite数据库
4. **RAG工具链**：基于向量检索的知识库查询系统
5. **Azure OpenAI/Ollama集成**：提供语言理解和生成能力
6. **对话线程管理**：支持多轮对话上下文保持

### 处理流程

```
查询输入 → 意图分类器 → 路由决策 → SQL节点/RAG节点/聊天节点 → 结果聚合 → 返回响应
```

## 技术栈

- **FastAPI**: Web服务框架
- **LangGraph**: 基于LangChain的图形处理框架
- **LangChain**: 大语言模型应用构建框架
- **OpenAI/Azure OpenAI**: 大语言模型服务
- **SQLite**: 关系型数据库
- **ChromaDB**: 向量数据库
- **Ollama**: 本地嵌入模型和LLM(可选)

## 安装和部署

### 前提条件

- Python 3.11+
- [可选] Ollama服务用于本地嵌入和LLM

### 安装步骤

1. 克隆仓库

```bash
git clone https://github.com/yourusername/BioSearch_Agent.git
cd BioSearch_Agent
```

2. 创建虚拟环境

```bash
conda create -n bioagent311 python=3.11 -y
conda activate bioagent311
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 配置环境变量

创建`.env`文件并填入以下内容:

```
OPENAI_API_KEY=your_openai_api_key
API_VERSION=2025-01-01-preview  # 根据Azure OpenAI设置调整
AZURE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
DATABASE_URL=sqlite:///./bioinfo.db
VECTOR_DB_PATH=./data/chroma
```

### 启动服务

```bash
uvicorn app.api.routes:app --reload
```

服务将在 http://127.0.0.1:8000 上运行

## API使用

### 健康检查

```
GET /healthz
```

### 数据库查询

```
GET /api/gse  # 获取所有GSE记录
GET /api/gse/{accession}  # 获取特定GSE记录
```

### 生物信息查询

```
POST /api/query
```

请求体:
```json
{
  "query": "查询GSE10000的信息",
  "model_provider": "openai",  // 可选，默认为openai，可选值：openai、ollama
  "model_name": "gpt-4o",      // 可选，默认为gpt-4o
  "thread_id": "uuid-string"   // 可选，用于保持对话上下文
}
```

响应:
```json
{
  "answer": "包含SQL和RAG结果的综合回答",
  "intent": "sql",
  "sql_result": "SQL查询结果",
  "rag_result": "RAG查询结果",
  "model_provider": "openai",
  "model_name": "gpt-4o",
  "thread_id": "uuid-string"
}
```

### 对话线程管理

```
GET /api/threads  # 获取所有对话线程ID
DELETE /api/threads/{thread_id}  # 删除特定对话线程
DELETE /api/threads  # 清空所有对话线程
```

### 模型信息

```
GET /api/models  # 获取可用的模型提供商和模型列表
```

## 自定义和扩展

### 添加新数据源

1. 在`app/db/schema.sql`中添加新表结构
2. 修改`app/tools/sql_toolkit.py`适配新数据

### 添加新知识库

1. 准备文档数据
2. 使用`app/data_loader/ingest_chromadb.py`脚本导入数据到向量数据库

```bash
# 方法1: 使用脚本直接运行
python -m app.data_loader.ingest_chromadb

# 方法2: 使用提供的初始化脚本
bash scripts/setup_vector_db.sh
```

系统默认使用`app/data_loader/load_docs.py`中定义的示例文档。如需添加自定义文档，可通过以下方法：

- **修改现有示例**：编辑`app/data_loader/load_docs.py`中的`load_documents()`函数，添加或替换现有的Document对象
- **自定义导入函数**：参考以下格式创建Document对象

```python
from langchain.schema import Document

# 示例：创建自定义文档
custom_doc = Document(
    page_content="文档内容...",
    metadata={"source": "文档来源", "topic": "文档主题"}
)
```

要使用Ollama进行嵌入，请确保已安装并启动Ollama服务：

```bash
# 安装Ollama (如果尚未安装)
brew install ollama  # macOS
# 拉取嵌入模型
ollama pull bge-m3:latest
# 启动Ollama服务
ollama serve
```

## 故障排除

### 常见问题

1. **OpenAI API连接问题**
   - 检查API密钥和Azure配置
   - 确认网络连接正常

2. **SQL查询错误**
   - 检查数据库是否正确初始化
   - 查看日志中的SQL语法错误

3. **向量存储问题**
   - 确保向量数据库目录存在且有写入权限
   - 检查Ollama服务状态(如果使用)
   - 如果遇到"初始化Ollama嵌入模型失败"错误，请确保已运行`ollama pull bge-m3:latest`
   - 系统会自动创建并初始化空向量数据库，如无法访问Ollama，将使用内存向量存储作为后备方案

4. **Ollama模型问题**
   - 确保Ollama服务已启动并可访问
   - 检查是否已拉取所需模型，例如：`ollama pull llama3`
   - 如果Ollama不可用，系统会自动回退到OpenAI模型

## 技术原理

### 意图分类

系统使用LLM分析查询意图，将查询分为以下几类:
- `sql`: 需要从数据库获取结构化数据
- `rag`: 需要从知识库获取信息
- `both`: 同时需要数据库和知识库信息
- `chat`: 普通聊天，与生物信息无关
- `unknown`: 无法确定意图

### 动态路由

基于LangGraph的条件边实现动态路由决策:
1. 从意图分类器开始
2. 根据分类结果选择路径
3. 可能直接进入SQL、RAG或聊天节点，或同时使用多个节点

### RAG实现

系统使用以下步骤实现检索增强生成:
1. 将文档嵌入到向量空间（使用Ollama的bge-m3模型或备用嵌入方案）
2. 基于查询相似度检索相关文档（使用Chroma向量数据库）
3. 将检索结果作为上下文提供给LLM
4. 生成基于上下文的回答

RAG处理流程通过`app/tools/rag_toolkit.py`中的`get_rag_chain`函数实现，主要包括：
- 向量存储初始化（包含自动降级机制）
- 相似度检索（返回最相关的文档）
- 提示模板格式化（将上下文与查询结合）
- 回答生成（使用Azure OpenAI或Ollama）

### 对话上下文保持

系统通过LangGraph的内存存储机制实现对话上下文保持：
1. 每个对话分配唯一的thread_id
2. 使用thread_id存储和检索对话历史
3. 支持删除特定对话线程或清空所有对话

## 性能和限制

- 当前系统使用内存SQLite数据库，适合中小规模数据
- 向量数据库存储在本地，可扩展性有限
- Azure API调用可能受到速率限制
- Ollama本地模型受限于本地硬件资源

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤:

1. Fork仓库
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

本项目使用MIT许可证 - 详见LICENSE文件 

## Docker部署

BioSearch Agent可以使用Docker进行部署，提供了两种Docker配置：生产环境和开发环境。

### 生产环境部署

使用标准Docker配置部署应用：

```bash
# 构建并启动容器
cd docker
docker-compose up --build

# 后台运行
docker-compose up -d --build
```

服务将在 http://localhost:8000 上运行

### 开发环境部署

开发环境包含额外的开发工具（git、sqlite3、vim等）和Python开发依赖：

```bash
# 构建并启动开发容器
cd docker
docker-compose -f docker-compose.dev.yml up --build

# 进入开发容器
docker exec -it docker_dev_1 bash

# 容器内运行应用
uvicorn app.api.routes:app --reload --host 0.0.0.0
```

开发环境还支持Jupyter Notebook，可通过 http://localhost:8888 访问。

### Docker环境变量配置

确保在运行Docker之前，已在项目根目录创建.env文件并填入所需的环境变量：

```
OPENAI_API_KEY=your_openai_api_key
API_VERSION=2025-01-01-preview
AZURE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
DATABASE_URL=sqlite:///./bioinfo.db
VECTOR_DB_PATH=./data/chroma
```

### Docker中的数据持久化

Docker配置中已设置卷映射，确保数据库和向量存储在容器重启后保持：

- SQLite数据库位于项目根目录的bioinfo.db
- 向量数据库存储在data/chroma目录

### Docker中使用Ollama

如果需要在Docker环境中使用Ollama进行嵌入，有两种方式：

#### 方式1：连接主机上的Ollama服务

1. 在主机上安装并启动Ollama：
```bash
# 安装Ollama (macOS)
brew install ollama

# 拉取所需模型
ollama pull bge-m3:latest

# 启动Ollama服务
ollama serve
```

2. 修改docker-compose文件，添加网络配置：
```yaml
# 在docker-compose.yml或docker-compose.dev.yml中添加
services:
  api:  # 或dev
    # ... 其他配置 ...
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

3. 修改代码中的Ollama连接设置：
```python
# 修改app/tools/rag_toolkit.py和app/data_loader/ingest_chromadb.py中的Ollama初始化
embeddings = OllamaEmbeddings(
    model="bge-m3",
    base_url="http://host.docker.internal:11434"  # 连接到主机的Ollama服务
)
```

#### 方式2：使用备用嵌入方法

如果无法使用Ollama，系统已配置备用嵌入方法，可以直接使用。

## 测试案例

以下是一些测试查询案例，可用于验证系统功能：

### 测试准备

在运行测试之前，请确保已完成以下准备工作：

#### 本地环境

```bash
# 1. 初始化SQLite数据库
bash scripts/setup_db.sh

# 2. 初始化向量数据库
bash scripts/setup_vector_db.sh

# 3. 启动服务
uvicorn app.api.routes:app --reload
```

#### Docker环境

```bash
# 1. 构建并启动Docker容器
cd docker
docker-compose up -d --build

# 2. 进入容器
docker exec -it docker_api_1 bash

# 3. 初始化数据库
sqlite3 ./bioinfo.db < app/db/schema.sql

# 4. 初始化向量数据库
python -m app.data_loader.ingest_chromadb

# 服务已自动启动在 http://localhost:8000
```

### SQL查询测试

```bash
# 使用curl测试SQL查询
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "GSE10000包含多少个样本?"}'

# 预期结果: 系统将查询数据库并返回GSE10000的样本数量
```

### RAG查询测试

```bash
# 使用curl测试RAG查询
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是RNA-seq技术?"}'

# 预期结果: 系统将从向量数据库检索相关信息并回答RNA-seq技术相关问题
```

### 混合查询测试

```bash
# 使用curl测试混合查询
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "GSE10000研究了什么，使用了什么平台?"}'

# 预期结果: 系统将结合数据库查询和知识库检索，提供完整回答
```

### 带记忆功能的多轮对话测试

```bash
# 第一轮对话 - 初始查询并保存返回的thread_id
RESPONSE=$(curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "GSE10000是什么?"}')
echo $RESPONSE
THREAD_ID=$(echo $RESPONSE | jq -r '.thread_id')
echo "对话线程ID: $THREAD_ID"

# 第二轮对话 - 使用相同的thread_id继续对话
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"它包含多少个样本?\", \"thread_id\": \"$THREAD_ID\"}"

# 第三轮对话 - 继续使用相同的thread_id，引用之前的对话内容
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"这个数据集的研究目的是什么?\", \"thread_id\": \"$THREAD_ID\"}"

# 预期结果: 系统能够记住之前的对话内容，理解"它"和"这个数据集"指的是GSE10000
```

### 切换模型的对话测试

```bash
# 使用OpenAI模型进行查询
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是单细胞测序?", "model_provider": "openai", "model_name": "gpt-4o"}'

# 使用Ollama模型进行查询（如果可用）
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是单细胞测序?", "model_provider": "ollama", "model_name": "llama3"}'
```

### 对话管理API测试

```bash
# 获取所有活跃的对话线程
curl http://127.0.0.1:8000/api/threads

# 删除特定对话线程
curl -X DELETE http://127.0.0.1:8000/api/threads/$THREAD_ID

# 清空所有对话线程
curl -X DELETE http://127.0.0.1:8000/api/threads
```

### API测试

```bash
# 测试健康检查
curl http://127.0.0.1:8000/healthz

# 获取所有GSE记录
curl http://127.0.0.1:8000/api/gse

# 获取特定GSE记录
curl http://127.0.0.1:8000/api/gse/GSE10000

# 获取可用的模型列表
curl http://127.0.0.1:8000/api/models
```

以上测试可以验证系统的各项功能，包括SQL查询、RAG查询、混合查询、多轮对话记忆功能和API端点。 