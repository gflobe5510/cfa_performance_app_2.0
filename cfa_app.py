import streamlit as st
import json
import random

st.set_page_config(page_title="CFA Practice App", layout="wide")
st.title("📊 CFA Practice App")

# Load Questions JSON
def load_questions():
    with open("questions.json", "r") as f:
        data = json.load(f)
    return data["questions"]

questions = load_questions()

# Initialize session state
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
    st.session_state.answered = False
    st.session_state.correct = None

# Get current question
if questions:
    q = questions[st.session_state.question_index]
    st.subheader(f"Q{st.session_state.question_index + 1}: {q['question']}")

    if not st.session_state.answered:
        user_choice = st.radio("Select your answer:", q["options"], key=f"question_{st.session_state.question_index}")
        if st.button("Submit"):
            correct_answer = q.get("correct_answer") or q.get("answer")
            is_correct = user_choice.strip().split(".")[0] == correct_answer.strip().split(".")[0]
            st.session_state.answered = True
            st.session_state.correct = is_correct
    else:
        if st.session_state.correct:
            st.success("Correct ✅")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q.get('correct_answer') or q.get('answer')}")
            if q.get("explanation"):
                st.markdown(f"**Explanation:** {q['explanation']}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Previous") and st.session_state.question_index > 0:
                st.session_state.question_index -= 1
                st.session_state.answered = False
        with col2:
            if st.button("Next") and st.session_state.question_index < len(questions) - 1:
                st.session_state.question_index += 1
                st.session_state.answered = False
else:
    st.warning("No questions available.")
