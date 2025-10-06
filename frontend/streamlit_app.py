import os, requests, datetime, io
import streamlit as st

BACKEND = f"http://localhost:{os.getenv('BACKEND_PORT', '8000')}"

st.set_page_config(page_title="AI Health Agent", page_icon="💪", layout="wide")

st.title("AI Health Agent")

tab1, tab2, tab3, tab4 = st.tabs(["식단 입력", "운동 데이터 업로드", "리포트", "코치에게 물어보기"])

with tab1:
    st.subheader("식단 텍스트 입력")
    diet_text = st.text_area("하루 식단을 붙여 넣으세요", height=160, placeholder="아침: ..., 점심: ...")
    if st.button("저장", type="primary"):
        r = requests.post(f"{BACKEND}/ingest/diet/text", json={"text": diet_text})
        st.success(r.json())

    st.subheader("식단 음성 업로드 (WAV/MP3 등)")
    audio = st.file_uploader("파일 업로드", type=["wav","mp3","m4a"])
    if st.button("음성 저장"):
        if audio is None:
            st.warning("파일을 선택하세요")
        else:
            files = {"file": (audio.name, audio.read(), audio.type)}
            r = requests.post(f"{BACKEND}/ingest/diet/audio", files=files)
            st.success(r.json())

with tab2:
    st.subheader("운동 데이터 CSV 업로드")
    source = st.selectbox("출처", ["strava", "google_fit", "manual"])
    csv_file = st.file_uploader("CSV 파일 선택", type=["csv"], key="csv")
    if st.button("업로드"):
        if csv_file is None:
            st.warning("CSV를 올려주세요")
        else:
            text = csv_file.getvalue().decode("utf-8")
            r = requests.post(f"{BACKEND}/ingest/exercise", json={"source": source, "csv_text": text})
            st.success(r.json())

with tab3:
    st.subheader("리포트 생성")
    day = st.date_input("날짜", value=datetime.date.today())
    if st.button("리포트 생성/보기", type="primary"):
        r = requests.post(f"{BACKEND}/report/daily", json={"day": str(day)})
        j = r.json()
        st.success({"ok": j.get("ok"), "day": j.get("day")})
        st.markdown(j.get("report_md", ""))

    st.divider()
    if st.button("RAG 재색인 (웹 출처)"):
        r = requests.post(f"{BACKEND}/rag/reindex")
        st.info(r.json())

with tab4:
    st.subheader("대화형 코치")
    msg = st.text_input("질문")
    if st.button("보내기"):
        r = requests.post(f"{BACKEND}/chat", json={"message": msg})
        st.markdown(r.json().get("answer",""))

st.caption("AZURE OpenAI, LangChain/LangGraph, FAISS, Streamlit, FastAPI, APScheduler")
