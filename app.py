
import streamlit as st
import time
import json
import re
from pypdf import PdfReader
from google import genai
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="AI Quiz Maker",
    page_icon="📝",
    layout="centered"
)

st.title("📝 AI Quiz Maker")
st.write("PDF अपलोड करें और हिंदी में अपना टेस्ट दें।")

if "questions" not in st.session_state:
    st.session_state.questions = []

if "started" not in st.session_state:
    st.session_state.started = False

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "deadline" not in st.session_state:
    st.session_state.deadline = 0


def make_quiz(text, count):
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )

    prompt = f"""
तुम हिंदी माध्यम के अनुभवी शिक्षक हो।

दिए गए PDF से ठीक {count} बहुविकल्पीय प्रश्न बनाओ।

भाषा और लिपि के नियम:
1. सभी प्रश्न, विकल्प और समाधान हिंदी की देवनागरी लिपि में लिखो।
2. Roman Hindi बिल्कुल मत लिखो।
3. उदाहरण: "Prakash ka veg kya hai?" गलत है।
4. "प्रकाश का वेग क्या है?" सही है।
5. उत्तर और समाधान भी देवनागरी हिंदी में होने चाहिए।
6. जरूरी वैज्ञानिक संकेत और गणितीय सूत्र वैसे ही रख सकते हो।

प्रश्न बनाने के नियम:
1. PDF से ही प्रश्न बनाओ।
2. हर प्रश्न के ठीक चार विकल्प हों।
3. हर प्रश्न का केवल एक सही उत्तर हो।
4. गणित में सूत्र, गणना और अंतिम उत्तर समझाओ।
5. विज्ञान में अवधारणा और कारण स्पष्ट करो।
6. PDF से बाहर की जानकारी मत जोड़ो।
7. उत्तर का अनुमान मत लगाओ।
8. answer में सही विकल्प का क्रमांक 0, 1, 2 या 3 हो।
9. ठीक {count} प्रश्न बनाओ।

केवल वैध JSON array लौटाओ।
Markdown या अतिरिक्त टेक्स्ट मत लिखो।

प्रत्येक प्रश्न का प्रारूप:
{{"question":"प्रश्न हिंदी में",
"options":["विकल्प 1","विकल्प 2","विकल्प 3","विकल्प 4"],
"answer":0,
"explanation":"समाधान चरण-दर-चरण हिंदी में"}}

PDF CONTENT:
{text[:25000]}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    result = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        response.text.strip()
    )

    data = json.loads(result)

    if not isinstance(data, list) or not data:
        raise ValueError("प्रश्न नहीं बन पाए।")

    if len(data) != count:
        raise ValueError("मॉडल ने मांगी गई संख्या में प्रश्न नहीं बनाए। कृपया दोबारा प्रयास करें।")

    for q in data:
        if (
            not isinstance(q, dict)
            or not isinstance(q.get("question"), str)
            or not isinstance(q.get("options"), list)
            or len(q["options"]) != 4
            or not all(isinstance(opt, str) for opt in q["options"])
            or not isinstance(q.get("answer"), int)
            or isinstance(q.get("answer"), bool)
            or q["answer"] not in [0, 1, 2, 3]
            or not isinstance(q.get("explanation"), str)
        ):
            raise ValueError("प्रश्न का प्रारूप गलत है। कृपया दोबारा प्रयास करें।")

    return data


if not st.session_state.started:
    pdf = st.file_uploader(
        "📄 PDF अपलोड करें",
        type=["pdf"]
    )

    count = st.number_input(
        "कितने प्रश्न चाहिए?",
        min_value=1,
        max_value=50,
        value=5,
        step=1
    )

    minutes = st.number_input(
        "टेस्ट का समय (मिनट)",
        min_value=1,
        max_value=180,
        value=5,
        step=1
    )

    if st.button("🚀 टेस्ट बनाएँ"):
        if pdf is None:
            st.warning("पहले PDF अपलोड करें।")
        else:
            try:
                reader = PdfReader(pdf)
                text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

                if len(text.strip()) < 50:
                    st.error(
                        "PDF में पढ़ने योग्य टेक्स्ट नहीं मिला।"
                    )
                else:
                    with st.spinner(
                        "हिंदी में प्रश्न और समाधान तैयार हो रहे हैं..."
                    ):
                        questions = make_quiz(text, int(count))

                    st.session_state.questions = questions
                    st.session_state.deadline = (
                        time.time() + int(minutes) * 60
                    )
                    st.session_state.started = True
                    st.session_state.submitted = False
                    st.rerun()

            except Exception as e:
                st.error(
                    "टेस्ट नहीं बन पाया। नीचे दिए गए संदेश को देखें।"
                )
                st.caption(str(e)[:500])


if (
    st.session_state.started
    and not st.session_state.submitted
):
    remaining = max(
        0,
        int(st.session_state.deadline - time.time())
    )

    if remaining > 0:
        st_autorefresh(
            interval=1000,
            key="quiz_timer"
        )

    st.subheader(
        f"⏳ बचा हुआ समय: {remaining // 60:02d}:{remaining % 60:02d}"
    )

    with st.form("quiz_form"):
        for i, q in enumerate(st.session_state.questions):
            st.markdown(
                f"**प्रश्न {i + 1}. {q['question']}**"
            )

            st.radio(
                "अपना उत्तर चुनें",
                options=range(4),
                format_func=lambda x, opts=q["options"]: opts[x],
                index=None,
                key=f"answer_{i}"
            )

        submitted = st.form_submit_button(
            "✅ टेस्ट जमा करें"
        )

    if submitted or remaining == 0:
        st.session_state.answers = {
            i: st.session_state.get(f"answer_{i}")
            for i in range(
                len(st.session_state.questions)
            )
        }
        st.session_state.submitted = True
        st.rerun()


if st.session_state.submitted:
    questions = st.session_state.questions
    answers = st.session_state.answers

    score = sum(
        answers.get(i) == q["answer"]
        for i, q in enumerate(questions)
    )

    st.header("📊 आपका परिणाम")

    st.metric(
        "आपका स्कोर",
        f"{score}/{len(questions)}"
    )

    percentage = score / len(questions) * 100

    st.write(f"प्रतिशत: {percentage:.1f}%")

    if percentage >= 80:
        st.success("बहुत बढ़िया! आपका प्रदर्शन शानदार है।")
    elif percentage >= 50:
        st.info("अच्छा प्रयास! थोड़ी और तैयारी करें।")
    else:
        st.warning(
            "चिंता न करें। समाधान पढ़ें और फिर अभ्यास करें।"
        )

    st.subheader("📖 उत्तर और विस्तृत समाधान")

    for i, q in enumerate(questions):
        st.markdown(
            f"**प्रश्न {i + 1}. {q['question']}**"
        )

        chosen = answers.get(i)

        if chosen is not None:
            st.write(
                "आपका उत्तर: " + q["options"][chosen]
            )
        else:
            st.write("आपका उत्तर: प्रयास नहीं किया")

        st.write(
            "सही उत्तर: " + q["options"][q["answer"]]
        )

        if chosen == q["answer"]:
            st.success("आपका उत्तर सही है।")
        else:
            st.error("आपका उत्तर गलत है।")

        st.markdown("**समाधान:**")
        st.write(
            q.get("explanation", "समाधान उपलब्ध नहीं है।")
        )
        st.divider()

    if st.button("🔄 नया टेस्ट दें"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


        
