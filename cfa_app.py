import streamlit as st
import json
import random
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="CFA Practice App", layout="wide")
st.title("📊 CFA Practice App")

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
    st.header("🎯 Practice by Topic")
    topic = st.selectbox("Choose a Topic", topics)
    difficulty = st.selectbox("Choose Difficulty", difficulties)

    filtered = [q for q in questions if q["topic"] == topic and q["difficulty"] == difficulty]

    if filtered:
        q = random.choice(filtered)
        st.subheader(q["question"])
        user_choice = st.radio("Select your answer:", q["options"], index=None)

        if st.button("Submit Answer"):
            correct = q.get("correct_answer", q.get("answer"))
            is_correct = user_choice and user_choice.split(".")[0] == correct.split(".")[0]
            st.session_state.results.append({
                "topic": q["topic"],
                "correct": is_correct
            })

            if is_correct:
                st.success("Correct! ✅")
            else:
                st.error(f"Incorrect ❌. Correct answer: {correct}")
                st.markdown(f"**Explanation**: {q.get('explanation', 'No explanation provided.')}")
    else:
        st.warning("No questions found for this combination.")

# Full Practice Exam
elif mode == "Full Practice Exam":
    st.header("🧪 Full Practice Exam")

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
            if selected and selected.split(".")[0] == correct.split(".")[0]:
                score += 1
                correct_bool = True
            else:
                correct_bool = False
            st.session_state.results.append({"topic": q["topic"], "correct": correct_bool})

        st.success(f"You scored {score}/50")
        del st.session_state.exam_questions
        del st.session_state.exam_answers

# Progress Tracker
elif mode == "Progress Tracker":
    st.header("📈 Progress Tracker")

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
