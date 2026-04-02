# smart-dev-assistant
智能研发助手-基于Agent于RAG的Java技术问答系统

## 项目简介
一个能回答 Spring Boot 技术问题，并能调用后端秒杀接口的智能助手。基于 LangChain 实现工具调用和简单 RAG 知识库，通过 Gradio 提供对话界面。

## 技术栈
- Python 3.9+
- LangChain
- ChromaDB（向量数据库）
- Gradio（聊天界面）
- Redis（对话记忆）

## 核心功能
- [x] 工具调用（查询优惠券、秒杀）
- [x] 多轮记忆（Redis）
- [x] RAG 知识库（Spring Boot 文档检索）
- [x] Gradio 对话界面

## 快速启动
1. 克隆项目：`git clone https://github.com/你的用户名/smart-dev-assistant.git`
2. 安装依赖：`pip install -r requirements.txt`
3. 配置 `.env` 文件（填写 API Key）
4. 确保黑马点评服务已启动
5. 运行 `python app.py`，访问 `http://127.0.0.1:7860`

## 项目亮点
- 将 Java 后端接口封装为 LangChain 工具，实现自然语言下单
- 集成 RAG 知识库，可回答技术问题
- 使用 Redis 存储对话历史，支持上下文
