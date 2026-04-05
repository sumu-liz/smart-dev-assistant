import gradio as gr
import pandas as pd
import os

from tools import query_vouchers, seckill_voucher

RESTAURANT_CSV_PATH = "docs/restaurant_reviews.csv"


def load_agent_backend():
    from agent import chat, rag_tool, recommend_restaurant

    return {
        "chat": chat,
        "rag_tool": rag_tool,
        "recommend_restaurant": recommend_restaurant,
    }


def run_agent_chat(message: str, history: list | None):
    history = history or []
    message = (message or "").strip()
    if not message:
        return history, ""

    try:
        backend = load_agent_backend()
        answer = backend["chat"](message)
    except Exception as exc:
        answer = f"后端初始化或调用失败：{exc}"
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]
    return history, ""


def run_restaurant_recommendation(requirement: str) -> str:
    requirement = (requirement or "").strip()
    if not requirement:
        return "请输入餐厅需求，例如：推荐一家适合朋友聚餐、环境好、预算100以内的餐厅。"
    try:
        backend = load_agent_backend()
        return backend["recommend_restaurant"].invoke(requirement)
    except Exception as exc:
        return f"餐厅推荐能力初始化失败：{exc}"


def run_project_qa(question: str) -> str:
    question = (question or "").strip()
    if not question:
        return "请输入项目知识相关问题，例如：黑马点评怎么防止超卖？"
    try:
        backend = load_agent_backend()
        return backend["rag_tool"].invoke(question)
    except Exception as exc:
        return f"项目知识库初始化失败：{exc}"


def run_coupon_query() -> str:
    return query_vouchers.invoke({})


def run_seckill(voucher_id: int | float | None) -> str:
    if voucher_id is None:
        return "请输入优惠券 ID。"
    return seckill_voucher.invoke({"voucher_id": int(voucher_id)})


def load_review_table() -> pd.DataFrame:
    df = pd.read_csv(RESTAURANT_CSV_PATH)
    useful_columns = [
        column
        for column in ["shop_name", "score", "review", "sentiment", "tags"]
        if column in df.columns
    ]
    return df[useful_columns]


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="黑马点评智能助手") as demo:
        gr.Markdown(
            """
            # 黑马点评智能助手
            一个前端同时展示项目问答、优惠券查询/秒杀、餐厅推荐和点评知识库。
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown(
                    """
                    **可直接体验的能力**
                    - 项目知识问答：如秒杀、防超卖、技术栈
                    - 优惠券服务：查询优惠券、按 ID 秒杀
                    - 餐厅推荐：按环境、价格、口味、聚餐等需求推荐
                    """
                )
            with gr.Column(scale=1):
                gr.Markdown(
                    """
                    **示例问题**
                    - 黑马点评怎么防止超卖？
                    - 帮我查优惠券
                    - 帮我秒杀 id 为 12 的优惠券
                    - 推荐一家适合约会、环境安静的餐厅
                    """
                )

        with gr.Tab("智能对话"):
            chatbot = gr.Chatbot(label="对话记录", height=480)
            user_input = gr.Textbox(
                label="你的输入",
                placeholder="输入任意需求，Agent 会自动调用项目知识、优惠券或餐厅推荐能力",
                lines=3,
            )
            with gr.Row():
                send_btn = gr.Button("发送", variant="primary")
                clear_btn = gr.Button("清空对话")

            send_btn.click(run_agent_chat, [user_input, chatbot], [chatbot, user_input])
            user_input.submit(run_agent_chat, [user_input, chatbot], [chatbot, user_input])
            clear_btn.click(lambda: [], outputs=chatbot)

        with gr.Tab("餐厅推荐"):
            gr.Markdown("输入客户需求，基于点评知识库返回推荐结果。")
            restaurant_query = gr.Textbox(
                label="客户需求",
                placeholder="例如：推荐一家适合朋友聚餐、环境好、预算100以内的餐厅",
                lines=3,
            )
            restaurant_result = gr.Markdown()
            restaurant_btn = gr.Button("生成推荐", variant="primary")
            restaurant_btn.click(
                run_restaurant_recommendation,
                inputs=restaurant_query,
                outputs=restaurant_result,
            )

        with gr.Tab("项目知识问答"):
            gr.Markdown("直接查询黑马点评项目知识库。")
            project_query = gr.Textbox(
                label="项目问题",
                placeholder="例如：黑马点评怎么防止超卖？",
                lines=3,
            )
            project_result = gr.Textbox(label="知识库检索结果", lines=10)
            project_btn = gr.Button("查询知识库", variant="primary")
            project_btn.click(run_project_qa, inputs=project_query, outputs=project_result)

        with gr.Tab("优惠券服务"):
            with gr.Row():
                query_btn = gr.Button("查询当前优惠券", variant="primary")
                voucher_output = gr.Textbox(label="服务结果", lines=12)
            query_btn.click(run_coupon_query, outputs=voucher_output)

            with gr.Row():
                voucher_id = gr.Number(label="优惠券 ID", precision=0, value=12)
                seckill_btn = gr.Button("执行秒杀")
            seckill_btn.click(run_seckill, inputs=voucher_id, outputs=voucher_output)

        with gr.Tab("点评数据"):
            gr.Markdown("当前用于推荐的餐厅点评数据。")
            review_table = gr.Dataframe(
                value=load_review_table(),
                interactive=False,
                wrap=True,
                label="餐厅点评知识库",
            )
            refresh_btn = gr.Button("刷新数据")
            refresh_btn.click(load_review_table, outputs=review_table)

    return demo


demo = build_demo()


if __name__ == "__main__":
    for proxy_key in [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ]:
        os.environ.pop(proxy_key, None)
    os.environ["NO_PROXY"] = "127.0.0.1,localhost,::1"
    os.environ["no_proxy"] = "127.0.0.1,localhost,::1"
    configured_port = os.getenv("GRADIO_SERVER_PORT")
    demo.launch(
        server_name="127.0.0.1",
        server_port=int(configured_port) if configured_port else None,
        share=False,
        inbrowser=False,
    )
