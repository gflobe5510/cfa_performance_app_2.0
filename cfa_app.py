import streamlit as st
import json
import random
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="CFA Practice App", layout="wide")
st.title("\U0001F4CA CFA Practice App")

# Load Questions JSON
def load_questions():
    with open("questions.json", "r") as f:
        data = json.load(f)
    return data["questions"]

questions = load_questions()
topics = sorted(set(q["topic"] for q in questions))
difficulties = ["Easy", "Medium", "Hard"]

# Initialize session state for tracking results
if "results" not in st.session_state:
    st.session_state.results = []

# Navigation
mode = st.sidebar.radio("Select Mode", ["Practice by Topic", "Full Practice Exam", "Progress Tracker"])

# Practice by Topic
if mode == "Practice by Topic":
    st.header("\U0001F3AF Practice by Topic")
    topic = st.selectbox("Choose a Topic", topics)
    difficulty = st.selectbox("Choose Difficulty", difficulties)

    filtered = [q for q in questions if q["topic"] == topic and q["difficulty"] == difficulty]

    if filtered:
        if "practice_index" not in st.session_state:
            st.session_state.practice_index = 0
            st.session_state.practice_locked = False
            st.session_state.practice_answer = None

        q = filtered[st.session_state.practice_index % len(filtered)]
        st.subheader(q["question"])

        user_choice = st.radio("Select your answer:", q["options"], index=None, key="practice_choice", disabled=st.session_state.practice_locked)

        if not st.session_state.practice_locked:
            submit_disabled = user_choice is None
            if st.button("Submit Answer", disabled=submit_disabled):
                correct = q.get("correct_answer", q.get("answer"))
                selected_letter = user_choice.split(".")[0].strip() if user_choice else ""
                correct_letter = correct.split(".")[0].strip() if correct else ""
                is_correct = selected_letter.upper() == correct_letter.upper()

                st.session_state.results.append({
                    "topic": q["topic"],
                    "correct": is_correct
                })

                if is_correct:
                    st.success("Correct! ✅")
                    st.session_state.practice_index += 1
                else:
                    st.error(f"Incorrect ❌. Correct answer: {correct}")
                    st.markdown(f"**Explanation**: {q.get('explanation', 'No explanation provided.')}")

                st.session_state.practice_locked = True
                st.session_state.practice_answer = user_choice
        else:
            if st.button("Next Question"):
                st.session_state.practice_index += 1
                st.session_state.practice_locked = False
                st.session_state.practice_answer = None
                st.experimental_rerun()
    else:
        st.warning("No questions found for this combination.")

# Full Practice Exam
elif mode == "Full Practice Exam":
    st.header("\U0001F9EA Full Practice Exam")

    if "exam_questions" not in st.session_state:
        st.session_state.exam_questions = random.sample(questions, 50)
        st.session_state.exam_answers = [None] * 50

    for i, q in enumerate(st.session_state.exam_questions):
        st.subheader(f"Q{i+1}: {q['question']}")
        st.session_state.exam_answers[i] = st.radio(f"Your Answer for Q{i+1}", q["options"], index=None, key=f"exam_{i}")

    if st.button("Finish Exam"):
        score = 0
        for i, q in enumerate(st.session_state.exam_questions):
            selected = st.session_state.exam_answers[i]
            correct = q.get("correct_answer", q.get("answer"))
            selected_letter = selected.split(".")[0].strip() if selected else ""
            correct_letter = correct.split(".")[0].strip() if correct else ""
            is_correct = selected_letter.upper() == correct_letter.upper()
            if is_correct:
                score += 1
            st.session_state.results.append({"topic": q["topic"], "correct": is_correct})

        st.success(f"You scored {score}/50")
        del st.session_state.exam_questions
        del st.session_state.exam_answers

# Progress Tracker
elif mode == "Progress Tracker":
    st.header("\U0001F4C8 Progress Tracker")

    if st.session_state.results:
        df = pd.DataFrame(st.session_state.results)
        summary = df.groupby("topic")["correct"].agg(["count", "sum"])
        summary["accuracy"] = summary["sum"] / summary["count"] * 100

        st.dataframe(summary)

        # Bar Chart
        fig, ax = plt.subplots()
        summary["accuracy"].plot(kind="bar", ax=ax, color=["green" if x >= 75 else "red" for x in summary["accuracy"]])
        ax.axhline(75, color="blue", linestyle="--", label="Benchmark (75%)")
        ax.set_ylabel("Accuracy %")
        ax.set_title("Accuracy by CFA Topic")
        ax.legend()
        st.pyplot(fig)
    else:
        st.info("No progress to show yet. Start practicing!")
