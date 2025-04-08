import streamlit as st
import json
import random
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ===== CONFIG =====
st.set_page_config(page_title="CFA Practice App", layout="wide")
st.title("📊 CFA Practice App")

# ===== CONSTANTS & SESSION STATE =====
TOPICS = ["Quantitative Methods", "Economics", "Portfolio Management"]  # Replace with your topics
DIFFICULTIES = ["Easy", "Medium", "Hard"]

if "results" not in st.session_state:
    st.session_state.results = []

# ===== HELPER FUNCTIONS =====
def load_questions() -> list:
    """Load questions from JSON with error handling."""
    try:
        with open(Path("questions.json"), "r") as f:
            return json.load(f).get("questions", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading questions: {str(e)}")
        return []

def validate_answer(selected: str, correct: str) -> bool:
    """Check if the selected answer (e.g., 'A. Option') matches the correct one."""
    return selected and correct and selected[0] == correct[0]

def reset_quiz():
    """Reset quiz state."""
    st.session_state.quiz = {
        "index": 0,
        "locked": False,
        "score": 0,
        "current_question": None
    }

# ===== MAIN APP =====
def practice_mode():
    st.header("🎯 Practice Mode")
    topic = st.selectbox("Topic", TOPICS)
    difficulty = st.selectbox("Difficulty", DIFFICULTIES)
    
    questions = [q for q in load_questions() 
                 if q["topic"] == topic and q["difficulty"] == difficulty]
    
    if not questions:
        st.warning("No questions found. Try another combo!")
        return

    if "quiz" not in st.session_state:
        reset_quiz()
        st.session_state.quiz["current_question"] = random.choice(questions)

    q = st.session_state.quiz["current_question"]
    st.subheader(q["question"])
    
    user_choice = st.radio(
        "Options:", 
        q["options"], 
        index=None,
        disabled=st.session_state.quiz["locked"]
    )

    if not st.session_state.quiz["locked"]:
        if st.button("Submit", disabled=not user_choice):
            is_correct = validate_answer(user_choice, q["correct_answer"])
            st.session_state.results.append({"topic": topic, "correct": is_correct})
            
            if is_correct:
                st.success("✅ Correct!")
                st.session_state.quiz["score"] += 1
            else:
                st.error(f"❌ Incorrect! Answer: {q['correct_answer']}")
                st.info(f"Explanation: {q.get('explanation', 'N/A')}")
            
            st.session_state.quiz["locked"] = True
    else:
        if st.button("Next Question"):
            reset_quiz()
            st.session_state.quiz["current_question"] = random.choice(questions)
            st.rerun()

def progress_tracker():
    st.header("📈 Progress Tracker")
    if not st.session_state.results:
        st.info("No data yet. Complete some questions!")
        return
    
    df = pd.DataFrame(st.session_state.results)
    summary = df.groupby("topic")["correct"].agg([
        ("Total", "count"), 
        ("Correct", "sum"),
        ("Accuracy", lambda x: f"{x.mean() * 100:.1f}%")
    ]).sort_values("Accuracy", ascending=False)
    
    st.dataframe(summary.style.highlight_between(subset=["Accuracy"], left=0, right=75, color="lightcoral"))
    
    # Plot
    fig, ax = plt.subplots()
    summary["Accuracy"].str.replace("%", "").astype(float).plot(
        kind="bar", 
        color=summary["Accuracy"].str.replace("%", "").astype(float).apply(
            lambda x: "green" if x >= 75 else "red"),
        ax=ax
    )
    ax.axhline(75, color="blue", linestyle="--")
    st.pyplot(fig)
    
    if st.button("Clear Data", type="primary"):
        st.session_state.results = []
        st.rerun()

# ===== SIDEBAR NAVIGATION =====
mode = st.sidebar.radio(
    "Mode", 
    ["Practice", "Progress Tracker"],  # Add "Exam" later!
    label_visibility="collapsed"
)

if mode == "Practice":
    practice_mode()
else:
    progress_tracker()
