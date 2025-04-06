import streamlit as st
import json
import random
import os
import sqlite3
import pandas as pd  # <- ADD THIS!


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
        user_choice = st.radio("Select your answer:", q["options"], index=None)
        if st.button("Submit"):
            is_correct = user_choice and user_choice.startswith(q["answer"])
            st.success("Correct! ✅" if is_correct else f"Incorrect ❌. Correct answer: {q['answer']}")
            st.markdown(f"**Explanation**: {q['explanation']}")
            c = db_conn.cursor()
            c.execute("INSERT INTO results (username, question_id, correct) VALUES (?, ?, ?)",
                      (username, q["id"], int(is_correct)))
            db_conn.commit()

# Mock Exam Mode
elif mode == "Mock Exam":
    st.header("🧪 Timed Mock Exam (10 Questions)")
    exam_qs = random.sample(questions, 10)
    score = 0

    for i, q in enumerate(exam_qs):
        st.subheader(f"Q{i + 1}: {q['question']}")
        user_choice = st.radio(f"Your Answer for Q{i + 1}:", q["options"], key=f"mock_{i}", index=None)
        if user_choice and user_choice.startswith(q["answer"]):
            score += 1

    if st.button("Finish Exam"):
        st.success(f"You scored {score}/10")
        for q in exam_qs:
            c = db_conn.cursor()
            c.execute("INSERT INTO results (username, question_id, correct) VALUES (?, ?, ?)",
                      (username, q["id"], None))
        db_conn.commit()

# Progress View
elif mode == "Progress":
    st.header("📈 Progress Tracker")
    df = None
    try:
        df = st.cache_data(lambda: pd.read_sql_query(f"SELECT * FROM results WHERE username = ?", db_conn, params=(username,)))()
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
