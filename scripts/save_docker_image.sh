#!/usr/bin/env bash

# 构建开发环境镜像
echo "构建开发环境镜像..."
cd "$(dirname "$0")/.."
docker-compose -f docker/docker-compose.dev.yml build

# 保存镜像
echo "保存镜像到biosearch-dev.tar..."
docker save -o biosearch-dev.tar $(docker images -q biosearch_agent_dev:latest)

echo "完成! 镜像已保存到 biosearch-dev.tar"
echo "使用 'docker load -i biosearch-dev.tar' 导入镜像" 