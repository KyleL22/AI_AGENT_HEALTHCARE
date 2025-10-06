from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

PLANNER_SYSTEM = """
You are a health-planner agent. Given user's diet/exercise summaries and RAG notes,
produce a compact plan: 1) key observations, 2) diet adjustments, 3) training focus,
4) 1-sentence motivation. Keep to bullet points.
"""

def get_planner_llm(deployment, api_key, endpoint):
    return AzureChatOpenAI(
        azure_deployment=deployment,
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-06-01",
        temperature=0.3,
    )

def make_plan(llm, diet_summary: str, exercise_summary: str, rag_notes: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM),
        ("user", "Diet Summary:\n{diet}\n\nExercise Summary:\n{ex}\n\nEvidence:\n{rag}\n\nMake plan.")
    ]).format_messages(diet=diet_summary, ex=exercise_summary, rag=rag_notes)
    return llm.invoke(prompt).content
