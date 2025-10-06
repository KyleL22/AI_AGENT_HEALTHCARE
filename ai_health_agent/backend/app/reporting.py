import os, pytz, datetime as dt
from apscheduler.schedulers.background import BackgroundScheduler
from .agents import build_graph
from .rag import chunk_and_ingest_text
from .rag import query_rag

TZ = pytz.timezone(os.getenv("TIMEZONE","Asia/Seoul"))
REPORTS_DIR = os.getenv("REPORTS_DIR","./data/reports")

os.makedirs(REPORTS_DIR, exist_ok=True)
graph = build_graph()
_scheduler = None

def _now():
    return dt.datetime.now(TZ)

def generate_report(user_id: str, diet_text: str = "", exercise_text: str = "", question: str = "하루 요약 및 권장안"):
    state = {"user_id": user_id, "diet_notes": diet_text, "exercise_notes": exercise_text, "question": question}
    res = graph.invoke(state)
    md = f"""# 일일 건강 리포트
- 사용자: {user_id}
- 생성 시각: {_now().strftime('%Y-%m-%d %H:%M')}

{res['answer']}
"""
    ts = _now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORTS_DIR, f"report_{user_id}_{ts}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    return path

def start_scheduler(app):
    global _scheduler
    if _scheduler:  # already running
        return

    hour = int(os.getenv("REPORT_HOUR","22"))
    _scheduler = BackgroundScheduler(timezone=TZ)
    _scheduler.add_job(lambda: generate_report("default_user"),
                       trigger="cron", hour=hour, minute=0, id="daily_report_default")
    _scheduler.start()

    @app.on_event("shutdown")
    def _shutdown():
        if _scheduler:
            _scheduler.shutdown(wait=False)
