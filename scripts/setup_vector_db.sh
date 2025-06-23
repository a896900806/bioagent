#!/usr/bin/env bash

# 确保在项目根目录运行
cd "$(dirname "$0")/.."

# 创建向量数据库目录（使用相对路径）
mkdir -p data/chroma

# 更新.env文件中的向量数据库路径
sed -i '' 's|VECTOR_DB_PATH=.*|VECTOR_DB_PATH=./data|' .env

# 检查Ollama是否已安装
if ! command -v ollama &> /dev/null; then
    echo "警告: 未找到Ollama命令。请先安装Ollama: https://ollama.com/download"
    echo "安装后，请运行: ollama pull bge-m3:latest"
    exit 1
fi

# 检查bge-m3模型是否已下载
echo "检查bge-m3模型..."
if ! ollama list | grep -q "bge-m3"; then
    echo "下载bge-m3模型..."
    ollama pull bge-m3:latest
else
    echo "bge-m3模型已存在"
fi

# 运行向量数据库初始化脚本
echo "开始创建向量数据库..."
python -m app.data_loader.ingest_chromadb

echo "向量数据库初始化完成!" 