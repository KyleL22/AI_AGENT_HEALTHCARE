import os, pathlib, io
from datetime import datetime, date
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from .models import DietIn, ExerciseIn, ReportRequest, ChatIn
from .config import *
from .parsers import parse_strava_csv, parse_google_fit_csv
from .agents import diet_agent, exercise_agent, recommender_agent, planner
from .rag.indexer import build_vectorstore
from .rag.retriever import retrieve
from apscheduler.schedulers.background import BackgroundScheduler
from .scheduler import start_scheduler

app = FastAPI(title="AI Health Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ensure data dirs
pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
pathlib.Path(VECTOR_DIR).mkdir(parents=True, exist_ok=True)

def _diet_file_path(day: str):
    return os.path.join(DATA_DIR, f"diet_{day}.txt")

def _exercise_file_path(day: str, source: str):
    return os.path.join(DATA_DIR, f"exercise_{source}_{day}.csv")

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

@app.post("/ingest/diet/text")
def ingest_diet_text(diet: DietIn):
    day = datetime.now().strftime("%Y-%m-%d")
    with open(_diet_file_path(day), "a", encoding="utf-8") as f:
        f.write((diet.text or "") + "\n")
    return {"ok": True, "day": day}

@app.post("/ingest/diet/audio")
async def ingest_diet_audio(file: UploadFile = File(...)):
    # Placeholder: save file; STT should be implemented via AOAI Audio if enabled.
    day = today_str()
    dest = os.path.join(DATA_DIR, f"diet_audio_{day}_{file.filename}")
    with open(dest, "wb") as f:
        f.write(await file.read())
    return {"ok": True, "saved": dest, "note": "Implement STT with AOAI and append transcript to diet file."}

@app.post("/ingest/exercise")
def ingest_exercise(ex: ExerciseIn):
    day = today_str()
    if ex.source.lower() == "strava":
        df = parse_strava_csv(ex.csv_text)
    elif ex.source.lower() == "google_fit":
        df = parse_google_fit_csv(ex.csv_text)
    else:
        df = parse_strava_csv(ex.csv_text)  # fallback

    path = _exercise_file_path(day, ex.source)
    df.to_csv(path, index=False, encoding="utf-8")
    return {"ok": True, "saved": path, "rows": len(df)}

@app.post("/rag/reindex")
def rag_reindex():
    # read URLs
    urls_path = os.path.join(DATA_DIR, "web_sources", "seed_urls.txt")
    with open(urls_path, "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f if x.strip()]
    ok = build_vectorstore(urls, VECTOR_DIR, AOAI_DEPLOY_EMBED_3_LARGE or AOAI_DEPLOY_EMBED_ADA, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT)
    return {"ok": ok, "count": len(urls)}

@app.post("/report/daily")
def make_daily_report(body: ReportRequest):
    day = body.day or today_str()

    raw_diet = ""
    df_text_path = _diet_file_path(day)
    if os.path.exists(df_text_path):
        raw_diet = open(df_text_path, "r", encoding="utf-8").read()

    # gather exercise CSVs for the day
    ex_texts = []
    for p in pathlib.Path(DATA_DIR).glob(f"exercise_*_{day}.csv"):
        ex_texts.append(open(p, "r", encoding="utf-8").read())
    ex_combined = "\n\n".join(ex_texts)

    # LLMs
    diet_llm = diet_agent.get_llm(AOAI_DEPLOY_GPT4O_MINI, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT)
    ex_llm = exercise_agent.get_llm(AOAI_DEPLOY_GPT4O_MINI, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT)
    plan_llm = planner.get_planner_llm(AOAI_DEPLOY_GPT4O_MINI, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT)
    rec_llm = recommender_agent.get_llm(AOAI_DEPLOY_GPT4O, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT)

    diet_summary = diet_agent.summarize_diet(diet_llm, raw_diet or "입력 없음")
    ex_summary = exercise_agent.summarize_exercise(ex_llm, ex_combined or "입력 없음")

    # retrieve evidence
    try:
        top = retrieve("건강한 식단 구성과 일일 운동 권장량", 5, VECTOR_DIR, AOAI_DEPLOY_EMBED_3_LARGE or AOAI_DEPLOY_EMBED_ADA, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT)
        rag_notes = "\n---\n".join([f"[{i+1}] {t}\n(source: {m.get('source')})" for i,(t,m) in enumerate(top)])
    except Exception as e:
        rag_notes = f"RAG retrieval failed: {e}"

    plan = planner.make_plan(plan_llm, diet_summary, ex_summary, rag_notes)
    recs = recommender_agent.recommend(rec_llm, rag_notes)

    report = f"""# 일일 건강 리포트 ({day})

## 식단 요약
{diet_summary}

## 운동 요약
{ex_summary}

## 코치 제안 (RAG 기반)
{recs}

## 실행 계획
{plan}
"""
    report_path = os.path.join(DATA_DIR, f"report_{day}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    return {"ok": True, "day": day, "report_path": report_path, "report_md": report}

@app.post("/chat")
def chat(chat: ChatIn):
    llm = diet_agent.get_llm(AOAI_DEPLOY_GPT4O_MINI, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT)
    # simple single-agent chat demo
    from langchain_core.prompts import ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a bilingual (Korean/English) friendly health coach. Keep answers concise and practical."),
        ("user", "{m}")
    ]).format_messages(m=chat.message)
    out = llm.invoke(prompt).content
    return {"ok": True, "answer": out}

# Start nightly scheduler (inside API process)
def generate_nightly():
    try:
        make_daily_report(ReportRequest())
    except Exception as e:
        print("Nightly report failed", e)

sched = start_scheduler(generate_nightly)
