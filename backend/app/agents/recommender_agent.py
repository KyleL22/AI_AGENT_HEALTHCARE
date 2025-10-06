from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

SYSTEM = """
You are a coach. Using retrieved evidence, suggest tomorrow's diet and a training plan.
Include '출처' list of sources used, referencing their domains.
"""

def get_llm(deployment, api_key, endpoint):
    return AzureChatOpenAI(
        azure_deployment=deployment,
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-06-01",
        temperature=0.4,
    )

def recommend(llm, rag_notes: str, constraints: str="") -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM),
        ("user", "Evidence:\n{rag}\n제약:{constraints}\n내일 제안 만들어줘.")
    ]).format_messages(rag=rag_notes, constraints=constraints or "없음")
    return llm.invoke(prompt).content
