import os, io, pandas as pd
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .schemas import IngestTextRequest, QueryRequest, ExerciseCSVMeta, GenericResponse
from .rag import chunk_and_ingest_text, query_rag
from .agents import build_graph
from .reporting import start_scheduler, generate_report

load_dotenv()

app = FastAPI(title="AI Health Agent Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

graph = build_graph()

@app.on_event("startup")
def _startup():
    start_scheduler(app)

@app.post("/ingest/text")
def ingest_text(req: IngestTextRequest):
    n = chunk_and_ingest_text(req.user_id, req.diet_text)
    return {"ok": True, "chunks": n}

@app.post("/ingest/exercise_csv")
def ingest_exercise_csv(meta: ExerciseCSVMeta = Form(...), file: UploadFile = File(...)):
    # Minimal parser: keep as raw table; downstream agents will read summaries via UI
    content = file.file.read()
    df = pd.read_csv(io.BytesIO(content))
    # Save raw
    save_path = f"./data/raw/{meta.user_id}_{meta.source}.csv"
    df.to_csv(save_path, index=False)
    # Add lightweight summary into RAG
    head = df.head(50).to_markdown()
    chunk_and_ingest_text(meta.user_id, f"운동 데이터({meta.source}) 샘플:
{head}")
    return {"ok": True, "rows": len(df), "saved": save_path}

@app.post("/report/run")
def run_report(user_id: str = Form("default_user"),
               diet_text: str = Form(""),
               exercise_text: str = Form("")):
    path = generate_report(user_id, diet_text, exercise_text)
    return {"ok": True, "path": path}

@app.get("/report/latest")
def latest_report(user_id: str = "default_user"):
    import glob, os, time
    files = sorted(glob.glob(f"./data/reports/report_{user_id}_*.md"))
    if not files:
        return {"ok": False, "msg": "no report yet"}
    latest = files[-1]
    with open(latest, "r", encoding="utf-8") as f:
        body = f.read()
    return {"ok": True, "path": latest, "body": body}

@app.post("/query")
def query(req: QueryRequest):
    hits = query_rag(req.user_id, req.question, k=4)
    diet = "\n\n".join([h["doc"] for h in hits[:2]])
    ex = "\n\n".join([h["doc"] for h in hits[2:]])
    state = {"user_id": req.user_id, "diet_notes": diet, "exercise_notes": ex, "question": req.question}
    res = graph.invoke(state)
    return {"ok": True, "answer": res["answer"], "context": [h["doc"] for h in hits]}
