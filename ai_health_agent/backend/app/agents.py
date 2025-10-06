import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .rag import query_rag

load_dotenv()

def llm(model_env: str = "AOAI_DEPLOY_GPT4O_MINI"):
    return AzureChatOpenAI(
        azure_deployment=os.getenv(model_env, "gpt-4o-mini"),
        openai_api_key=os.getenv("AOAI_API_KEY"),
        azure_endpoint=os.getenv("AOAI_ENDPOINT"),
        openai_api_version="2024-02-01",
        temperature=0.2,
    )

# ----- Prompts -----
DIET_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are DietAgent. Summarize meals, estimate macros (rough), detect issues (sugar/sodium), "
     "and cite evidence if helpful. Respond in Korean, concise bullet points."),
    MessagesPlaceholder("messages"),
])

EXERCISE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are ExerciseAgent. Summarize workload (volume, intensity, frequency). "
     "Recommend next-day plan with RPE/HR zones. Respond in Korean."),
    MessagesPlaceholder("messages"),
])

COACH_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are CoachAgent. Merge Diet/Exercise insights + RAG context into one actionable plan. "
     "Flag any contraindications (e.g., hypertension→sodium limit). Include 3 web-backed tips. "
     "Format as Markdown sections in Korean."),
    MessagesPlaceholder("messages"),
])

# ----- State -----
class S(dict):
    user_id: str
    question: str
    diet_notes: str
    exercise_notes: str
    rag_snippets: List[str]
    answer: str

def diet_node(state: S):
    diet_input = state.get("diet_notes","")
    q = state.get("question","오늘 식단 요약")
    chat = DIET_PROMPT | llm()
    out = chat.invoke({"messages":[("human", f"{q}\n\n식단:
{diet_input}")]})

    state["diet_notes"] = out.content
    return state

def exercise_node(state: S):
    ex_input = state.get("exercise_notes","")
    q = state.get("question","오늘 운동 요약")
    chat = EXERCISE_PROMPT | llm()
    out = chat.invoke({"messages":[("human", f"{q}\n\n운동:
{ex_input}")]})

    state["exercise_notes"] = out.content
    return state

def rag_node(state: S):
    user_id = state["user_id"]
    q = state.get("question","건강 팁")
    hits = query_rag(user_id, q, k=4)
    state["rag_snippets"] = [h["doc"] for h in hits]
    return state

def coach_node(state: S):
    chat = COACH_PROMPT | llm("AOAI_DEPLOY_GPT4O")
    diet = state.get("diet_notes","")
    ex = state.get("exercise_notes","")
    ctx = "\n\n".join(state.get("rag_snippets", []))
    prompt = f"""사용자 질문: {state.get('question','오늘 리포트')}

[식단 요약]
{diet}

[운동 요약]
{ex}

[RAG 문헌 요약]
{ctx}

위 정보들을 종합해서 actionable한 가이드를 한국어 Markdown으로 작성.
"""
    out = chat.invoke({"messages":[("human", prompt)]})
    state["answer"] = out.content
    return state

def build_graph():
    g = StateGraph(S)
    g.add_node("diet", diet_node)
    g.add_node("exercise", exercise_node)
    g.add_node("rag", rag_node)
    g.add_node("coach", coach_node)

    g.set_entry_point("diet")
    g.add_edge("diet", "exercise")
    g.add_edge("exercise", "rag")
    g.add_edge("rag", "coach")
    g.add_edge("coach", END)

    mem = MemorySaver()
    return g.compile(checkpointer=mem)
