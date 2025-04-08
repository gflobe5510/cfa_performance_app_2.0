import streamlit as st
import json
import random
import os
import sqlite3
import pandas as pd

st.set_page_config(page_title="CFA Practice App", layout="wide")
st.title("\U0001F4CA CFA Practice App 2.0")

# Load Questions JSON
def load_questions():
    with open("questions.json", "r") as f:
        data = json.load(f)
    return data["questions"]

questions = load_questions()
topics = sorted(set(q["topic"] for q in questions))
difficulties = sorted(set(q["difficulty"] for q in questions))

# SQLite DB setup
def init_db():
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results (
                username TEXT, 
                question_id TEXT, 
                correct INTEGER, 
                flagged INTEGER DEFAULT 0
                )''')
    conn.commit()
    return conn

db_conn = init_db()

# Sidebar login
username = st.sidebar.text_input("Enter your name", help="To begin practicing, type your name and hit Enter.")
if not username:
    st.info("To begin practicing, type your name and hit Enter.")
    st.stop()

if "started" not in st.session_state:
    if st.sidebar.button("\U0001F680 Start App"):
        st.session_state.started = True
    else:
        st.markdown("### Welcome to CFA Practice App 2.0!")
        st.markdown("To begin, enter your name in the sidebar and click 'Start App'.")
        st.stop()

st.success(f"Welcome, {username}! \U0001F389")
st.markdown("To begin, choose **Practice** or **Mock Exam** from the menu on the left. You can track your results afterward in the **Progress** tab.")

mode = st.sidebar.radio("Choose Mode", ["Practice", "Mock Exam", "Progress"])

# PRACTICE MODE
if mode == "Practice":
    st.header("\U0001F3AF Practice Questions")
    selected_topic = st.selectbox("Select Topic", topics)
    selected_difficulty = st.selectbox("Select Difficulty", difficulties)

    filtered = [q for q in questions if q["topic"] == selected_topic and q["difficulty"] == selected_difficulty]
    if not filtered:
        st.warning("No questions found for this selection.")
        st.stop()

    if "practice_index" not in st.session_state:
        st.session_state.practice_index = 0
    if "practice_answers" not in st.session_state:
        st.session_state.practice_answers = {}
    if "practice_submitted" not in st.session_state:
        st.session_state.practice_submitted = {}

    q = filtered[st.session_state.practice_index % len(filtered)]
    q_key = f"practice_q_{q['id']}"
    submitted = st.session_state.practice_submitted.get(q_key, False)
    st.subheader(q["question"])

    user_choice = st.radio("Select your answer:", q["options"], index=None, key=q_key, disabled=submitted)

    if user_choice and not submitted:
        if st.button("Submit Answer"):
            correct_answer = q.get("correct_answer") or q.get("answer")
            is_correct = user_choice.strip() == correct_answer.strip()
            st.session_state.practice_answers[q_key] = user_choice
            st.session_state.practice_submitted[q_key] = True

            c = db_conn.cursor()
            c.execute("INSERT INTO results (username, question_id, correct) VALUES (?, ?, ?)",
                      (username, q["id"], int(is_correct)))
            db_conn.commit()

            if is_correct:
                st.success("Correct! ✅")
                st.session_state.practice_index += 1
                st.experimental_rerun()
            else:
                st.error(f"Incorrect ❌. Correct answer: {correct_answer}")
                if q.get("explanation"):
                    st.markdown(f"**Explanation**: {q['explanation']}")
    elif submitted:
        prev_choice = st.session_state.practice_answers.get(q_key)
        st.info(f"You selected: {prev_choice}")
        if prev_choice.strip() == (q.get("correct_answer") or q.get("answer")).strip():
            st.success("Correct ✅")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q.get('correct_answer') or q.get('answer')}")
            if q.get("explanation"):
                st.markdown(f"**Explanation**: {q['explanation']}")

    col1, col2 = st.columns(2)
    if col1.button("⬅ Previous"):
        st.session_state.practice_index = (st.session_state.practice_index - 1) % len(filtered)
        st.experimental_rerun()
    if col2.button("➡ Next"):
        st.session_state.practice_index = (st.session_state.practice_index + 1) % len(filtered)
        st.experimental_rerun()

# MOCK EXAM MODE
elif mode == "Mock Exam":
    st.header("\U0001F9EA Timed Mock Exam (50 Questions)")
    if "exam_qs" not in st.session_state:
        st.session_state.exam_qs = random.sample(questions, min(50, len(questions)))
        st.session_state.score = 0
        st.session_state.answered = [None] * len(st.session_state.exam_qs)

    for i, q in enumerate(st.session_state.exam_qs):
        st.subheader(f"Q{i + 1}: {q['question']}")
        st.session_state.answered[i] = st.radio(f"Your Answer for Q{i + 1}:", q["options"], index=None, key=f"mock_{i}")

    if st.button("Finish Exam"):
        score = sum(1 for i, q in enumerate(st.session_state.exam_qs)
                    if st.session_state.answered[i] and st.session_state.answered[i].strip() == q.get("correct_answer", q.get("answer")).strip())
        st.success(f"You scored {score}/{len(st.session_state.exam_qs)}")
        for i, q in enumerate(st.session_state.exam_qs):
            is_correct = st.session_state.answered[i] and st.session_state.answered[i].strip() == q.get("correct_answer", q.get("answer")).strip()
            c = db_conn.cursor()
            c.execute("INSERT INTO results (username, question_id, correct) VALUES (?, ?, ?)",
                      (username, q["id"], int(bool(is_correct))))
            db_conn.commit()
        del st.session_state.exam_qs
        del st.session_state.answered

# PROGRESS
elif mode == "Progress":
    st.header("\U0001F4C8 Progress Tracker")
    try:
        df = pd.read_sql_query("SELECT * FROM results WHERE username = ?", db_conn, params=(username,))
    except:
        df = None

    if df is not None and not df.empty:
        total = df.shape[0]
        correct = df[df.correct == 1].shape[0]
        accuracy = round(correct / total * 100, 2) if total > 0 else 0
        st.metric("Total Attempted", total)
        st.metric("Correct", correct)
        st.metric("Accuracy (%)", accuracy)
    else:
        st.info("Answer some questions to see your stats!")
