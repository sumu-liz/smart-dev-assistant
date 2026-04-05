import os
import pandas as pd
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from tools import query_vouchers, seckill_voucher

os.environ["CHROMA_TELEMETRY"] = "0"
load_dotenv()

PROJECT_DB_DIR = "./chroma_db"
PROJECT_COLLECTION = "project_knowledge"
RESTAURANT_DB_DIR = "./chroma_reviews_db"
RESTAURANT_COLLECTION = "restaurant_reviews"
RESTAURANT_CSV_PATH = "docs/restaurant_reviews.csv"

llm = ChatOpenAI(model="qwen-plus", temperature=0)
embedding = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
)

knowledge = """
# 黑马点评项目知识
## 秒杀功能
- 使用Redis预减库存，提高并发性能
- 用Redis分布式锁防止超卖
- 一人一单：根据用户ID做锁
- 异步下单消息队列削峰
## 优惠券规则
- 一个用户一天只能抢一张
- 库存不足直接秒杀失败
- 支付超时自动取消订单
## 技术栈
SpringBoot, MySQL, Redis, RabbitMQ, MyBatis-Plus
"""


def build_project_retriever():
    docs = [Document(page_content=knowledge, id="heima_doc_1")]
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    chunk_ids = [f"project_chunk_{idx}" for idx, _ in enumerate(chunks)]
    project_store = Chroma.from_documents(
        documents=chunks,
        ids=chunk_ids,
        embedding=embedding,
        persist_directory=PROJECT_DB_DIR,
        collection_name=PROJECT_COLLECTION,
    )
    return project_store.as_retriever(search_kwargs={"k": 2})


def auto_label(text: str) -> str:
    prompt = f"""
请判断点评的情感并提取关键词。
返回格式：情感,关键词1|关键词2

示例：
点评：这家店环境很好，味道也不错
返回：正面,环境好|味道好

点评：菜品一般，价格偏贵
返回：中性,价格|味道一般

点评：服务太差，环境很脏
返回：负面,服务差|环境差

现在请判断下面的点评：
{text}
"""
    response = llm.invoke(prompt)
    return response.content.splitlines()[0].strip()


def ensure_review_labels(df: pd.DataFrame) -> pd.DataFrame:
    has_sentiment = "sentiment" in df.columns
    has_tags = "tags" in df.columns
    needs_labeling = (
        not has_sentiment
        or not has_tags
        or df["sentiment"].fillna("").eq("").any() #fillna("")，把空值替换成空字符串，.eq("")再判断每个单元格是否为空，.any()如果任意一个是空就返回True
        or df["tags"].fillna("").eq("").any()
    )

    if not needs_labeling:
        return df

    sentiments = []
    tags_list = []
    for _, row in df.iterrows():
        current_sentiment = str(row.get("sentiment", "")).strip() #取这一行的sentiment值，如果没有这一列或之不存在就返回空字符串
        current_tags = str(row.get("tags", "")).strip()
        if current_sentiment and current_tags and current_sentiment.lower() != "nan" and current_tags.lower() != "nan":
            sentiments.append(current_sentiment)
            tags_list.append(current_tags)
            continue

        label = auto_label(str(row["review"]))
        if "," in label:
            sentiment, tags = label.split(",", 1) #split()方法用于将字符串分割成子字符串列表，最多分割一次
        else:
            sentiment, tags = "中性", ""
        sentiments.append(sentiment.strip())
        tags_list.append(tags.strip())

    df["sentiment"] = sentiments
    df["tags"] = tags_list
    df.to_csv(RESTAURANT_CSV_PATH, index=False, encoding="utf-8") #index=false就是不添加第一列 行号
    return df


def build_restaurant_retriever():
    df = pd.read_csv(RESTAURANT_CSV_PATH)
    df = ensure_review_labels(df)

    review_docs = []
    review_ids = []
    for idx, row in df.iterrows(): #iterrows()函数是pandas库中用于遍历DataFrame行的一个方法。它返回一个生成器，生成器每次迭代返回一个包含行索引和行数据的元组。
        tags = str(row.get("tags", "")).replace("|", "、")
        sentiment = str(row.get("sentiment", "中性"))
        score = row.get("score", "")
        review_docs.append(
            Document(
                page_content=(
                    f"餐厅：{row['shop_name']}\n"
                    f"评分：{score}\n"
                    f"点评：{row['review']}\n"
                    f"情感：{sentiment}\n"
                    f"关键词：{tags}"
                ),
                metadata={
                    "shop_name": row["shop_name"],
                    "score": score,
                    "sentiment": sentiment,
                    "row_id": idx,
                },
            )
        )
        review_ids.append(f"restaurant_review_{idx}")

    restaurant_store = Chroma.from_documents(
        documents=review_docs,
        ids=review_ids,
        embedding=embedding,
        persist_directory=RESTAURANT_DB_DIR,
        collection_name=RESTAURANT_COLLECTION,
    )
    return restaurant_store.as_retriever(search_kwargs={"k": 4})


project_retriever = build_project_retriever()
restaurant_retriever = build_restaurant_retriever()


@tool
def rag_tool(query: str) -> str:
    """当你需要查询黑马点评项目相关知识时，使用这个工具。输入是用户的问题，输出是从项目知识库里找到的相关内容。"""
    docs = project_retriever.invoke(query)
    if not docs:
        return "未找到相关信息。"
    return "\n\n".join(doc.page_content for doc in docs)


@tool
def recommend_restaurant(query: str) -> str:
    """当用户提出口味、环境、服务、价格、聚餐等就餐需求时，使用这个工具推荐合适的餐厅。输入是用户需求，输出是推荐结果。"""
    docs = restaurant_retriever.invoke(query)
    if not docs:
        return "没有找到符合需求的餐厅点评。"

    context = "\n\n".join(doc.page_content for doc in docs) #元素拼成一个字符串
    prompt = f"""
你是餐厅推荐助手。请根据用户需求和检索到的真实点评，给出最多 3 家餐厅推荐。

用户需求：
{query}

候选点评：
{context}

输出要求：
1. 优先推荐真正符合需求的餐厅，不要编造信息。
2. 每家餐厅一行，格式：餐厅名：推荐理由。
3. 推荐理由要结合口味、环境、服务、价格或上菜速度等具体信息。
4. 如果候选里有明显负面评价，也要谨慎说明。
"""
    return llm.invoke(prompt).content.strip()


tools = [query_vouchers, seckill_voucher, rag_tool, recommend_restaurant]
memory = MemorySaver()
agent = create_react_agent(model=llm, tools=tools, checkpointer=memory)


def chat(message: str) -> str:
    config = {"configurable": {"thread_id": "user-1"}} #配置参数，thread_id是用户会话的标识，可以用来区分不同用户的对话历史
    response = agent.invoke({"messages": [("user", message)]}, config=config)
    return response["messages"][-1].content #返回最后一个消息的内容


if __name__ == "__main__":
    print("帮我查优惠券")
    print(chat("帮我查优惠券"))

    print("帮我秒杀id为12的优惠券")
    print(chat("帮我秒杀id为12的优惠券"))

    print("黑马点评怎么防止超卖？")
    print(chat("黑马点评怎么防止超卖？"))

    print("推荐一家适合朋友聚餐、环境好一点的餐厅")
    print(chat("推荐一家适合朋友聚餐、环境好一点的餐厅"))
