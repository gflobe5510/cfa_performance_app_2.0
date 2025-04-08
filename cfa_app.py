import streamlit as st
import json

st.set_page_config(page_title="CFA Practice App", layout="wide")
st.title("📊 CFA Practice App Basic")

# Load Questions JSON
def load_questions():
    with open("questions.json", "r") as f:
        data = json.load(f)
    return data["questions"]

questions = load_questions()

# Select question
if questions:
    q = questions[0]  # Just show first question for now
    st.subheader(q["question"])
    user_choice = st.radio("Select your answer:", q["options"])

    if st.button("Submit Answer"):
        correct = q.get("correct_answer") or q.get("answer")
        if user_choice.strip() == correct.strip():
            st.success("Correct ✅")
        else:
            st.error(f"Incorrect ❌. Correct answer: {correct}")
            if q.get("explanation"):
                st.markdown(f"**Explanation:** {q['explanation']}")
else:
    st.warning("No questions available.")
