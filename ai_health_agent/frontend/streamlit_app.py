import os, requests, streamlit as st

BACKEND = os.getenv("BACKEND_URL","http://localhost:8000")

st.set_page_config(page_title="AI Health Agent", layout="wide")
st.title("🏥 AI Health Agent")

with st.sidebar:
    st.header("데이터 업로드")
    uid = st.text_input("User ID", "default_user")

    st.subheader("식단 텍스트")
    diet_text = st.text_area("하루 식단(자유서술)", height=150)
    if st.button("식단 텍스트 인덱싱"):
        r = requests.post(f"{BACKEND}/ingest/text", json={"user_id": uid, "diet_text": diet_text})
        st.success(r.json())

    st.subheader("운동 CSV 업로드")
    file = st.file_uploader("Strava/Google Fit CSV", type=["csv"])
    source = st.selectbox("소스", ["strava", "google_fit", "other"])
    if file and st.button("운동 CSV 업로드"):
        files = {"file": (file.name, file.getvalue(), "text/csv")}
        data = {"user_id": uid, "source": source}
        r = requests.post(f"{BACKEND}/ingest/exercise_csv", files=files, data=data)
        st.success(r.json())

col1, col2 = st.columns(2)

with col1:
    st.subheader("RAG 질의")
    q = st.text_input("질문", "저녁 식단 추천과 내일 운동 가이드 알려줘")
    if st.button("질의하기"):
        r = requests.post(f"{BACKEND}/query", json={"user_id": uid, "question": q})
        data = r.json()
        st.markdown("### 답변")
        st.write(data.get("answer",""))
        with st.expander("컨텍스트"):
            for i, c in enumerate(data.get("context", []), 1):
                st.markdown(f"**[{i}]** {c}")

with col2:
    st.subheader("리포트")
    if st.button("지금 생성(수동)"):
        r = requests.post(f"{BACKEND}/report/run", data={"user_id": uid, "diet_text": "", "exercise_text": ""})
        st.success(r.json())
    if st.button("최근 리포트 보기"):
        r = requests.get(f"{BACKEND}/report/latest", params={"user_id": uid})
        data = r.json()
        if data.get("ok"):
            st.markdown(data["body"])
        else:
            st.warning("리포트가 아직 없습니다.")
