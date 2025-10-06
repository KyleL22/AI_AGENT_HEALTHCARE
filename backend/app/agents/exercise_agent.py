from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

SYSTEM = """
You are a workout analyst. Given today's workout sets from CSV (Strava/Google Fit),
summarize load, intensity, and cardio minutes. Detect over/under training.
Output in Korean bullet points.
"""

def get_llm(deployment, api_key, endpoint):
    return AzureChatOpenAI(
        azure_deployment=deployment,
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-06-01",
        temperature=0.2,
    )

def summarize_exercise(llm, structured_text: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM),
        ("user", "운동기록 CSV 텍스트:\n{csv}\n요약해줘.")
    ]).format_messages(csv=structured_text)
    return llm.invoke(prompt).content
