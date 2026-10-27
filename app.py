import streamlit as st

st.set_page_config(page_title="AI Quiz Maker", page_icon="📝")

st.title("📝 My AI Quiz Maker")
st.write("PDF se apni quiz banao!")

pdf = st.file_uploader(
    "Apni questions wali PDF upload karo",
    type=["pdf"]
)

st.subheader("Test Settings")

question_count = st.number_input(
    "Kitne questions chahiye?",
    min_value=1,
    value=20,
    step=1
)

time_limit = st.number_input(
    "Test ka samay (minutes)",
    min_value=1,
    value=20,
    step=5
)

st.write(f"Questions: {question_count}")
st.write(f"Time: {time_limit} minutes")

if pdf is not None:
    st.success("PDF upload ho gayi!")
    st.info("Agla step: PDF se questions nikalna aur quiz banana.")

st.caption("AI Quiz Maker - Version 1")
