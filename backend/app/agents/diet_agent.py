from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

SYSTEM = """
You are a nutrition analyst. Summarize the day's diet into macros trends and
flag issues (sugar spikes, low protein, fiber). Output in Korean, concise bullets.
"""

def get_llm(deployment, api_key, endpoint):
    return AzureChatOpenAI(
        azure_deployment=deployment,
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-06-01",
        temperature=0.2,
    )

def summarize_diet(llm, raw_text: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM),
        ("user", "오늘 식단:\n{diet}\n요약해줘.")
    ]).format_messages(diet=raw_text)
    return llm.invoke(prompt).content
