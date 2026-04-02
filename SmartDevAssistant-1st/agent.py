import os
#读取.env文件中的API Key，不让密匙暴露在代码中
from dotenv import load_dotenv
#导入大模型，给Agent装大脑
from langchain_openai import ChatOpenAI
#第一个创建思考型智能体，第二个执行器
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
#导入tools里面的查询优惠券工具
from tools import query_vouchers,seckill_voucher
from langchain.memory import ConversationBufferMemory


# 加载 .env 中的 API Key
load_dotenv()

# 初始化大模型（确保 .env 中有 OPENAI_API_KEY）。temperature=0->回答更准确、不乱编
llm = ChatOpenAI(
    model="qwen-plus",
    temperature=0
)
memory=ConversationBufferMemory(
    memory_key="chat_history",
#返回LangChain标准消息格式
    return_messages=True
)

# MessagesPlaceholder是LangChain库中用于处理聊天消息列表的一个占位符类
prompt = ChatPromptTemplate.from_messages([
    ("system","你是一个擅长调用工具的助手,记住上下文"),
    MessagesPlaceholder(variable_name="chat_history"), #记忆位置
    ("user","{input}"),
    MessagesPlaceholder("agent_scratchpad")
])

# 绑定工具
tools = [query_vouchers,seckill_voucher]
agent = create_openai_tools_agent(llm, tools, prompt)

# 创建执行器
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory,verbose=True)
chat_history=[]

# def chat_with_memory(message):
#     global chat_history
#     result = agent_executor.invoke({
#         "input":message,
#         "chat_history":chat_history
#     })
#     #把对话存进记忆
#     chat_history.append(("user",message))
#     chat_history.append(("assistant",result["output"]))
#     return result["output"]
def chat(message:str)->str:
    response=agent_executor.invoke({
        "input":message
    })
    return response["output"]

if __name__ == "__main__":
    # result = agent_executor.invoke({"input": "帮我查一下优惠券","chat_history":[]})
    print("帮我查优惠券")
    print(chat("帮我查优惠券"))

    print("帮我秒杀id为12的优惠券")
    print(chat("帮我秒杀id为12的优惠券"))

    # print(chat_with_memory("帮我查一下优惠券"))
    # print(chat_with_memory("帮我秒杀id为11的"))
