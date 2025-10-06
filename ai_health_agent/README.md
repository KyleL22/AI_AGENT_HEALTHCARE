# AI Health Agent (Streamlit + FastAPI + LangGraph + RAG)

> ✅ 목표: 식단(텍스트/음성), 운동 데이터를 받아 **매일 밤 22:00 (Asia/Seoul)** 건강 리포트를 생성하고, RAG 기반으로 웹 출처를 인용하며 **맞춤형 식단/운동**을 제안하는 에이전트.

## 주요 기능
- 입력: TXT/음성(옵션), CSV(운동기록: Strava/Google Fit 호환)
- Multi-Agent( LangGraph ):
  - **DietAgent**: 식단 요약/영양 추정 → RAG 지식과 결합
  - **ExerciseAgent**: 운동 부하 요약 → 권장 운동 볼륨 산출
  - **CoachAgent**: 최종 권장안 정제 및 금기(질환/알러지 등) 체크
- **RAG**: Chroma(로컬) + Azure OpenAI Embeddings
- **리포트 스케줄러**: APScheduler로 22:00 자동 생성 (Markdown → 저장)
- **UI**: Streamlit 업로드/조회, 백엔드 API 연동
- **패키징**: FastAPI(backend), Streamlit(frontend), Docker Compose

> ⚠️ 보안: 실제 키를 `.env`(로컬)에만 보관하세요. 본 저장소에는 `.env.example`만 포함됩니다. 본 문서에 포함된 **과거 키가 노출되었다면 즉시 폐기/재발급** 하세요.

---

## 폴더 구조
```
ai_health_agent/
├─ backend/
│  └─ app/
│     ├─ main.py
│     ├─ agents.py
│     ├─ rag.py
│     ├─ reporting.py
│     └─ schemas.py
├─ data/
│  ├─ raw/
│  ├─ vectorstore/
│  └─ reports/
├─ frontend/
│  └─ streamlit_app.py
├─ docker_compose.yml
├─ requirements.txt
├─ .env.example
└─ README.md
```

## 빠른 시작 (로컬)
```bash
# 1) 파이썬 환경
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) 환경변수 설정
cp .env.example .env
# .env 파일을 열어 Azure OpenAI 설정과 EMBEDDING DEPLOY NAME 등 입력

# 3) 백엔드 실행
uvicorn backend.app.main:app --reload --port 8000

# 4) 프론트 실행
streamlit run frontend/streamlit_app.py --server.port 8501
```

## Docker 실행
```bash
docker compose up --build
```

## API 요약
- `POST /ingest/text` : (diet_text) 식단 텍스트를 벡터화하여 DB에 누적
- `POST /ingest/exercise_csv` : (csv) 운동 CSV(예: Strava/Google Fit) 업로드
- `POST /report/run` : 즉시 보고서 생성(22:00 스케줄 외 수동 실행)
- `GET  /report/latest` : 최근 리포트 조회
- `POST /query` : 사용자의 질문에 대해 RAG + Multi-Agent로 응답

## 평가 포인트 정리
- **Prompt Engineering**: 역할 프롬프트/체인-오브-쏘트, few-shot 템플릿 포함
- **LangChain & LangGraph Multi-Agent**: ReAct-style Tool 사용, memory 적용
- **RAG**: Chroma + Azure Embeddings, 전처리/청크/ingest API 제공
- **서비스/패키징**: Streamlit UI, FastAPI 백엔드, Docker Compose
- **운영 고려**: .env, 로깅, 예외처리, 스케줄러, 모듈화
