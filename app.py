
import streamlit as st
import time
import json
import re
from pypdf import PdfReader
from google import genai
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="AI Quiz Maker", page_icon="📝")
st.title("📝 AI Quiz Maker")
st.write("PDF upload karo aur apna test do!")

if "questions" not in st.session_state:
    st.session_state.questions = []
if "started" not in st.session_state:
    st.session_state.started = False
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "deadline" not in st.session_state:
    st.session_state.deadline = 0

def make_quiz(text, count):
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    prompt = f"""
PDF ke content se exactly {count} MCQ banao.
Har question ke 4 options hon. Correct answer aur explanation bhi do.
Sirf valid JSON array return karo, markdown nahi.
Har item ka format:
{{"question":"Question","options":["A","B","C","D"],
"answer":0,"explanation":"Explanation"}}
answer 0 se 3 tak integer ho.

PDF CONTENT:
{text[:25000]}
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash", contents=prompt
    )
    result = re.sub(r"^```(?:json)?\s*|\s*```$", "",
                    response.text.strip())
    data = json.loads(result)
    if not isinstance(data, list) or not data:
        raise ValueError("Questions nahi ban paye.")
    for q in data:
        if (len(q.get("options", [])) != 4
                or q.get("answer") not in [0, 1, 2, 3]):
            raise ValueError("Question format galat hai.")
    return data

if not st.session_state.started:
    pdf = st.file_uploader("PDF upload karo", type=["pdf"])
    count = st.number_input("Kitne questions?", 1, 50, 5)
    minutes = st.number_input("Test time (minutes)", 1, 180, 5)

    if st.button("🚀 Quiz Banao"):
        if pdf is None:
            st.warning("Pehle PDF upload karo.")
        else:
            try:
                reader = PdfReader(pdf)
                text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
                if len(text.strip()) < 50:
                    st.error("PDF mein readable text nahi mila.")
                else:
                    with st.spinner("AI quiz bana raha hai..."):
                        st.session_state.questions = make_quiz(
                            text, int(count)
                        )
                    st.session_state.deadline = (
                        time.time() + int(minutes) * 60
                    )
                    st.session_state.started = True
                    st.rerun()
            except Exception as e:
                st.error("Quiz nahi ban paya. Settings check karo.")
                st.caption(str(e)[:250])

if st.session_state.started and not st.session_state.submitted:
    remaining = max(
        0, int(st.session_state.deadline - time.time())
    )
    st_autorefresh(interval=1000, key="timer")
    st.subheader(f"⏳ Time: {remaining // 60:02d}:{remaining % 60:02d}")

    with st.form("quiz"):
        for i, q in enumerate(st.session_state.questions):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            st.radio(
                "Answer chuno",
                range(4),
                format_func=lambda x, o=q["options"]: o[x],
                index=None,
                key=f"a{i}"
            )
        submit = st.form_submit_button("Test Submit Karo")

    if submit or remaining == 0:
        st.session_state.answers = {
            i: st.session_state.get(f"a{i}")
            for i in range(len(st.session_state.questions))
        }
        st.session_state.submitted = True
        st.rerun()

if st.session_state.submitted:
    qs = st.session_state.questions
    score = sum(
        st.session_state.answers.get(i) == q["answer"]
        for i, q in enumerate(qs)
    )
    st.header("📊 Tumhara Result")
    st.metric("Score", f"{score}/{len(qs)}")
    st.write(f"Percentage: {score / len(qs) * 100:.1f}%")

    for i, q in enumerate(qs):
        st.markdown(f"**Q{i+1}. {q['question']}**")
        chosen = st.session_state.answers.get(i)
        st.write("Tumhara answer: " +
                 (q["options"][chosen] if chosen is not None
                  else "Attempt nahi kiya"))
        st.write("Correct answer: " + q["options"][q["answer"]])
        st.write("Explanation: " + q.get("explanation", ""))
        st.divider()

    if st.button("Naya Test"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

        
