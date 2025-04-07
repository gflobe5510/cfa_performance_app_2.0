import streamlit as st
import json
import random
import os
import sqlite3
import pandas as pd

st.set_page_config(page_title="CFA Study App", layout="wide")
st.title("📊 CFA Practice App 2.0")

# Load Questions JSON
def load_questions():
    with open("questions.json", "r") as f:
        data = json.load(f)
    return data["questions"]

# Load questions
questions = load_questions()
topics = sorted(set(q["topic"] for q in questions))
difficulties = sorted(set(q["difficulty"] for q in questions))

# SQLite DB setup
def init_db():
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results (
                 username TEXT,
                 question_id INTEGER,
                 correct INTEGER,
                 flagged INTEGER DEFAULT 0
                 )''')
    conn.commit()
    return conn

db_conn = init_db()

# Sidebar user setup
username = st.sidebar.text_input("Enter your name")
if not username:
    st.stop()

# App Tabs
mode = st.sidebar.radio("Choose Mode", ["Practice", "Mock Exam", "Progress"])

# Practice Mode
if mode == "Practice":
    st.header("🎯 Practice Questions")
    selected_topic = st.selectbox("Select Topic", topics)
    selected_difficulty = st.selectbox("Select Difficulty", difficulties)

    filtered = [q for q in questions if q["topic"] == selected_topic and q["difficulty"] == selected_difficulty]
    if not filtered:
        st.warning("No questions found for this selection.")
    else:
        q = random.choice(filtered)
        st.subheader(q["question"])
        user_choice = st.radio("Select your answer:", q["options"], index=None, key="practice_choice")
        if st.button("Submit"):
            is_correct = user_choice and user_choice.split(".")[0] == q["answer"]

correct_answer = q.get("answer")
if correct_answer is None:
    import logging
    logging.warning(f"[Missing Answer] Question ID: {q.get('id', 'unknown')}")
if is_correct:
    st.success("Correct! ✅")
else:
    st.error(f"Incorrect ❌. Correct answer: {correct_answer if correct_answer else 'N/A'}")

st.markdown(f"**Explanation**: {q['explanation']}")
            c = db_conn.cursor()
            c.execute("INSERT INTO results (username, question_id, correct) VALUES (?, ?, ?)",
                      (username, q["id"], int(is_correct)))
            db_conn.commit()

# Mock Exam Mode
elif mode == "Mock Exam":
    st.header("🧪 Timed Mock Exam (50 Questions)")
    if "exam_qs" not in st.session_state:
        st.session_state.exam_qs = random.sample(questions, min(50, len(questions)))
        st.session_state.score = 0
        st.session_state.answered = [None] * len(st.session_state.exam_qs)

    for i, q in enumerate(st.session_state.exam_qs):
        st.subheader(f"Q{i + 1}: {q['question']}")
        user_choice = st.radio(f"Your Answer for Q{i + 1}:", q["options"], index=None, key=f"mock_{i}")
        st.session_state.answered[i] = user_choice

    if st.button("Finish Exam"):
        score = sum(1 for i, q in enumerate(st.session_state.exam_qs)
                    if st.session_state.answered[i] and st.session_state.answered[i].split(".")[0] == q["answer"])
        st.success(f"You scored {score}/{len(st.session_state.exam_qs)}")
        for i, q in enumerate(st.session_state.exam_qs):
            c = db_conn.cursor()
            is_correct = st.session_state.answered[i] and st.session_state.answered[i].split(".")[0] == q["answer"]
            c.execute("INSERT INTO results (username, question_id, correct) VALUES (?, ?, ?)",
                      (username, q["id"], int(bool(is_correct))))
        db_conn.commit()
        del st.session_state.exam_qs
        del st.session_state.answered

# Progress View
elif mode == "Progress":
    st.header("📈 Progress Tracker")
    df = None
    try:
        df = pd.read_sql_query("SELECT * FROM results WHERE username = ?", db_conn, params=(username,))
    except:
        st.warning("No progress data yet.")

    if df is not None and not df.empty:
        total = df.shape[0]
        correct = df[df.correct == 1].shape[0]
        accuracy = round(correct / total * 100, 2) if total > 0 else 0
        st.metric("Total Attempted", total)
        st.metric("Correct", correct)
        st.metric("Accuracy (%)", accuracy)
    else:
        st.info("Answer some questions to see your stats!")