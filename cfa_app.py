import streamlit as st
import pandas as pd
import json

with open('questions.json', 'r') as file:
    data = json.load(file)
    print(data)
import random
import sqlite3
from datetime import datetime
from fpdf import FPDF
import plotly.express as px

st.set_page_config(page_title="CFA Study App", layout="wide")
DB_PATH = "results.db"

@st.cache_data
def load_questions():
    """Load questions from the questions.json file."""
    try:
        with open("questions.json", "r") as f:
            questions = json.load(f)
            return questions.get("questions", [])
    except json.JSONDecodeError as e:
        st.error(f"Failed to decode JSON: {e}")
        return []
    except FileNotFoundError as e:
        st.error(f"File not found: {e}")
        return []
    except Exception as e:
        st.error(f"Failed to load questions.json: {e}")
        return []

questions = load_questions()

def execute_db_query(query, params=()):
    """Execute a database query with parameters."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")

def log_result(username, q, user_answer, correct):
    """Log the result of a user's answer to the database."""
    query = """
        CREATE TABLE IF NOT EXISTS exam_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            question TEXT,
            user_answer TEXT,
            correct_answer TEXT,
            is_correct INTEGER,
            topic TEXT,
            difficulty TEXT,
            timestamp TEXT
        )
    """
    execute_db_query(query)

    query = """
        INSERT INTO exam_results (
            username, question, user_answer, correct_answer, is_correct,
            topic, difficulty, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        username, q['question'], user_answer, q['answer'],
        int(correct), q['topic'], q['difficulty'], datetime.now().isoformat()
    )
    execute_db_query(query, params)

def show_completion_animation():
    """Show completion animation for the exam."""
    st.markdown("### 🎉 Exam Complete! Great job!")
    st.balloons()

st.sidebar.title("CFA Study App")
username = st.sidebar.text_input("Enter your name", value="Guest")
section = st.sidebar.radio("Navigate", ["🏠 Home", "🧠 Practice", "📊 Dashboard", "⏱️ Mock Exam", "🔁 Review Mistakes"])

st.title("📘 CFA Mastery Platform")

if not questions:
    st.warning("Questions not available. Please ensure questions.json is uploaded.")
elif section == "🏠 Home":
    st.success("Welcome to your CFA Practice App. Use the sidebar to begin.")
elif section == "🧠 Practice":
    st.header("🧠 Practice Questions")
    topic = st.selectbox("Select Topic", sorted(set(q["topic"] for q in questions)))
    difficulty = st.selectbox("Select Difficulty", ["easy", "medium", "hard"])
    count = st.slider("Number of Questions", 1, 10, 5)
    filtered = [q for q in questions if q["topic"] == topic and q["difficulty"] == difficulty]
    sample = random.sample(filtered, min(count, len(filtered)))

    for i, q in enumerate(sample):
        st.markdown(f"**Q{i+1}: {q['question']}**")
        answer = st.radio("Choose an answer:", [""] + q["options"], key=f"practice_{i}", index=0)
        if st.button(f"Submit Q{i+1}", key=f"submit_{i}"):
            if answer == "":
                st.warning("Please select an answer before submitting.")
            elif answer.startswith(q["answer"]):
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Incorrect. Correct answer: {q['answer']}")
            st.info(q["explanation"])
            log_result(username, q, answer, answer.startswith(q["answer"]))

elif section == "📊 Dashboard":
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM exam_results WHERE username = ?", conn, params=(username,))
        conn.close()
        if df.empty:
            st.info("No data yet. Answer some questions to see your dashboard.")
        else:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["date"] = df["timestamp"].dt.date
            daily = df.groupby("date")["is_correct"].mean().reset_index()
            daily["Accuracy %"] = daily["is_correct"] * 100
            st.subheader("📈 Accuracy Over Time")
            st.plotly_chart(px.line(daily, x="date", y="Accuracy %", markers=True))
            topic_perf = df.groupby("topic")["is_correct"].mean().reset_index()
            topic_perf["Score (%)"] = topic_perf["is_correct"] * 100
            st.subheader("📚 Score by Topic")
            st.plotly_chart(px.bar(topic_perf, x="topic", y="Score (%)"))
    except Exception as e:
        st.error(f"Failed to load dashboard data: {e}")

elif section == "⏱️ Mock Exam":
    if "mock_questions" not in st.session_state:
        if st.button("Start Mock Exam"):
            st.session_state.mock_questions = random.sample(questions, 50)
            st.session_state.mock_index = 0
            st.session_state.mock_score = 0
    else:
        idx = st.session_state.mock_index
        if idx < 50:
            q = st.session_state.mock_questions[idx]
            st.markdown(f"**Q{idx+1}: {q['question']}**")
            answer = st.radio("Choose an answer:", [""] + q["options"], key=f"mock_{idx}", index=0)
            if st.button("Submit Answer", key=f"submit_mock_{idx}"):
                correct = answer and answer.startswith(q["answer"])
                if correct:
                    st.success("✅ Correct!")
                    st.session_state.mock_score += 1
                else:
                    st.error(f"❌ Incorrect. Correct: {q['answer']}")
                st.info(q["explanation"])
                log_result(username, q, answer, correct)
                st.session_state.mock_index += 1
                st.experimental_rerun()
        else:
            show_completion_animation()
            st.success(f"🏁 Final Score: {st.session_state.mock_score} / 50")
            del st.session_state.mock_questions
            del st.session_state.mock_index
            del st.session_state.mock_score

elif section == "🔁 Review Mistakes":
    try:
        conn = sqlite3.connect(DB_PATH)
        missed = pd.read_sql("SELECT * FROM exam_results WHERE username = ? AND is_correct = 0", conn, params=(username,))
        conn.close()
        if missed.empty:
            st.info("✅ No missed questions to review.")
        else:
            for i, row in missed.iterrows():
                st.markdown(f"**Q{i+1}: {row['question']}**")
                st.error(f"Your Answer: {row['user_answer']} | Correct: {row['correct_answer']}")
                st.info("Explanation: See CFA curriculum.")
    except Exception as e:
        st.error(f"Review error: {e}")
