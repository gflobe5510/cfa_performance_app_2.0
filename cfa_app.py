import streamlit as st
import json
import random
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict  # NEW: Type hints for clarity

# Constants for session state keys (NEW: Avoid typos)
PRACTICE_INDEX = "practice_index"
PRACTICE_LOCKED = "practice_locked"
EXAM_QUESTIONS = "exam_questions"
EXAM_ANSWERS = "exam_answers"
RESULTS = "results"

# Configure page
st.set_page_config(page_title="CFA Practice App", layout="wide")
st.title("\U0001F4CA CFA Practice App")

# --- Helper Functions (NEW: Refactored for reusability) ---
def load_questions() -> List[Dict]:
    """Load questions from JSON with error handling."""
    try:
        with open("questions.json", "r") as f:
            data = json.load(f)
        return data.get("questions", [])
    except FileNotFoundError:
        st.error("Error: 'questions.json' not found. Please check the file path.")
        return []
    except json.JSONDecodeError:
        st.error("Error: Invalid JSON format in 'questions.json'.")
        return []

def validate_answer(selected: str, correct_answer: str) -> bool:
    """Check if the selected answer matches the correct one (compares first letters)."""
    if not selected or not correct_answer:
        return False
    return selected[0] == correct_answer[0]  # Compare 'A' vs 'B' (prefixes)

def reset_practice_state():
    """Reset practice mode session state."""
    st.session_state[PRACTICE_INDEX] = 0
    st.session_state[PRACTICE_LOCKED] = False
    st.session_state.practice_answer = None

# --- Initialize Data ---
questions = load_questions()
topics = sorted(set(q["topic"] for q in questions)) if questions else []
difficulties = ["Easy", "Medium", "Hard"]

# Initialize session state (IMPROVED: Centralized)
if RESULTS not in st.session_state:
    st.session_state[RESULTS] = []

# --- Navigation ---
mode = st.sidebar.radio("Select Mode", ["Practice by Topic", "Full Practice Exam", "Progress Tracker"])

# --- Practice by Topic ---
if mode == "Practice by Topic":
    st.header("\U0001F3AF Practice by Topic")
    topic = st.selectbox("Choose a Topic", topics)
    difficulty = st.selectbox("Choose Difficulty", difficulties)

    filtered = [q for q in questions if q["topic"] == topic and q["difficulty"] == difficulty]

    if not filtered:
        st.warning("No questions found. Try another topic/difficulty combo!")
    else:
        # Initialize session state for practice mode
        if PRACTICE_INDEX not in st.session_state:
            reset_practice_state()

        q = filtered[st.session_state[PRACTICE_INDEX] % len(filtered)]
        st.subheader(q["question"])

        user_choice = st.radio(
            "Select your answer:", 
            q["options"], 
            index=None, 
            key="practice_choice", 
            disabled=st.session_state[PRACTICE_LOCKED]
        )

        if not st.session_state[PRACTICE_LOCKED]:
            if st.button("Submit Answer", disabled=user_choice is None):
                is_correct = validate_answer(user_choice, q.get("correct_answer", q.get("answer")))
                
                # Record result
                st.session_state[RESULTS].append({
                    "topic": q["topic"],
                    "correct": is_correct
                })

                # Show feedback
                if is_correct:
                    st.success("Correct! ✅")
                    st.session_state[PRACTICE_INDEX] += 1
                else:
                    st.error(f"Incorrect ❌. Correct answer: {q.get('correct_answer', q.get('answer'))}")
                    st.markdown(f"**Explanation**: {q.get('explanation', 'No explanation provided.')}")

                st.session_state[PRACTICE_LOCKED] = True
        else:
            if st.button("Next Question"):
                reset_practice_state()
                st.experimental_rerun()

# --- Full Practice Exam ---
elif mode == "Full Practice Exam":
    st.header("\U0001F9EA Full Practice Exam")

    if EXAM_QUESTIONS not in st.session_state:
        st.session_state[EXAM_QUESTIONS] = random.sample(questions, min(50, len(questions)))  # NEW: Handles <50 questions
        st.session_state[EXAM_ANSWERS] = [None] * len(st.session_state[EXAM_QUESTIONS])

    for i, q in enumerate(st.session_state[EXAM_QUESTIONS]):
        st.subheader(f"Q{i+1}: {q['question']}")
        st.session_state[EXAM_ANSWERS][i] = st.radio(
            f"Your Answer for Q{i+1}", 
            q["options"], 
            index=None, 
            key=f"exam_{i}"
        )

    if st.button("Finish Exam"):
        score = 0
        for i, q in enumerate(st.session_state[EXAM_QUESTIONS]):
            is_correct = validate_answer(
                st.session_state[EXAM_ANSWERS][i],
                q.get("correct_answer", q.get("answer"))
            )
            if is_correct:
                score += 1
            st.session_state[RESULTS].append({"topic": q["topic"], "correct": is_correct})

        st.success(f"You scored {score}/{len(st.session_state[EXAM_QUESTIONS])}")
        del st.session_state[EXAM_QUESTIONS]  # NEW: Cleanup
        del st.session_state[EXAM_ANSWERS]

# --- Progress Tracker ---
elif mode == "Progress Tracker":
    st.header("\U0001F4C8 Progress Tracker")

    if st.session_state[RESULTS]:
        df = pd.DataFrame(st.session_state[RESULTS])
        summary = df.groupby("topic")["correct"].agg(["count", "sum"])
        summary["accuracy"] = (summary["sum"] / summary["count"] * 100).round(1)
        summary = summary.sort_values("accuracy", ascending=False)  # NEW: Sorted

        # Overall accuracy metric (NEW)
        overall_accuracy = df["correct"].mean() * 100
        st.metric("Overall Accuracy", f"{overall_accuracy:.1f}%")

        st.dataframe(summary.style.highlight_between(subset=["accuracy"], left=0, right=75, color="lightcoral"))

        # Visualization
        fig, ax = plt.subplots()
        summary["accuracy"].plot(
            kind="bar", 
            ax=ax, 
            color=["green" if x >= 75 else "red" for x in summary["accuracy"]]
        )
        ax.axhline(75, color="blue", linestyle="--", label="Benchmark (75%)")
        ax.set_ylabel("Accuracy %")
        ax.set_title("Accuracy by CFA Topic")
        ax.legend()
        st.pyplot(fig)

        # NEW: Reset progress button
        if st.button("Reset Progress"):
            st.session_state[RESULTS] = []
            st.success("Progress reset!")
            st.experimental_rerun()
    else:
        st.info("No progress to show yet. Start practicing!")
