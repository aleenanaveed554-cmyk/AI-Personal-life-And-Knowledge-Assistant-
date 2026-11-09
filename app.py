import os
import io
import json
import sqlite3
import hashlib
from datetime import datetime, date

import streamlit as st
from groq import Groq

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

st.set_page_config(
    page_title="LifeMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(93, 63, 211, .13), transparent 28%),
        radial-gradient(circle at 90% 20%, rgba(0, 196, 255, .10), transparent 25%),
        #080b14;
    color: #f4f7ff;
}
section[data-testid="stSidebar"] {
    background: rgba(10, 13, 25, .96);
    border-right: 1px solid rgba(255,255,255,.08);
}
.hero {
    padding: 42px 36px;
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 28px;
    background: linear-gradient(135deg, rgba(91,60,220,.23), rgba(11,16,34,.92));
    box-shadow: 0 20px 70px rgba(0,0,0,.25);
}
.hero h1 {
    font-size: clamp(2.2rem, 5vw, 4.5rem);
    line-height: 1;
    margin: 0 0 16px;
    font-weight: 800;
    letter-spacing: -2px;
}
.hero p {
    color: #b9c2d8;
    max-width: 760px;
    font-size: 1.08rem;
    line-height: 1.7;
}
.badge {
    display:inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(124,92,255,.15);
    border: 1px solid rgba(124,92,255,.35);
    color: #cfc6ff;
    font-size: .82rem;
    font-weight: 700;
    margin-bottom: 18px;
}
.feature {
    min-height: 155px;
    padding: 22px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,.08);
    background: rgba(255,255,255,.035);
}
.feature .icon { font-size: 28px; }
.feature h3 { margin: 10px 0 6px; font-size: 1.05rem; }
.feature p { color: #9fa9c0; font-size: .88rem; line-height: 1.5; }
.card {
    padding: 20px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,.08);
    background: rgba(255,255,255,.035);
}
.small { color:#9fa9c0; font-size:.86rem; }
.metric {
    padding: 18px;
    border-radius: 18px;
    background: rgba(255,255,255,.035);
    border: 1px solid rgba(255,255,255,.07);
}
.metric b { font-size: 1.8rem; }
div[data-testid="stButton"] > button {
    border-radius: 12px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ---------- Database ----------
DB = "lifemind.db"

def db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

conn = db()
cur = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'General',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT NOT NULL,
    due_date TEXT,
    completed INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS dates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    event_date TEXT NOT NULL,
    notes TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
""")
conn.commit()

# ---------- AI ----------
def get_client():
    key = os.getenv("GROQ_API_KEY")
    try:
        key = st.secrets.get("GROQ_API_KEY", key)
    except Exception:
        pass
    return Groq(api_key=key) if key else None

def ask_ai(prompt, system=None):
    client = get_client()
    if not client:
        return "Groq API key is not configured. Add GROQ_API_KEY to Streamlit secrets or environment variables."
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.5,
            max_tokens=1200,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI error: {e}"

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🧠 LifeMind AI")
    st.caption("Your personal knowledge companion")
    st.divider()

    page = st.radio(
        "Workspace",
        [
            "🏠 Home",
            "💬 AI Chat",
            "📝 Notes",
            "📄 Documents",
            "✅ Tasks & Goals",
            "📅 Important Dates",
            "📚 Learning",
            "📊 Dashboard",
        ],
    )

    st.divider()
    st.caption("Built with Python • Streamlit • Groq")
    st.caption("Your local notes/tasks are stored in SQLite.")

# ---------- Home ----------
if page == "🏠 Home":
    st.markdown("""
    <div class="hero">
      <div class="badge">PERSONAL AI KNOWLEDGE OS</div>
      <h1>Think less. Remember more.</h1>
      <p>
        LifeMind AI brings your notes, documents, tasks, learning and everyday
        knowledge into one intelligent workspace powered by Groq.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    if st.button("🚀 Get Started", type="primary", use_container_width=False):
        st.session_state["started"] = True
        st.success("Welcome to LifeMind AI — choose a workspace from the sidebar.")

    st.write("")
    st.markdown("### Everything you need in one place")
    features = [
        ("💬", "AI Chat", "Ask questions, brainstorm ideas, explain topics and plan your day."),
        ("📝", "Personal Notes", "Save ideas, memories, knowledge and important information."),
        ("📄", "Document Q&A", "Upload PDFs or text files and ask questions about their content."),
        ("🔎", "Smart Search", "Quickly find saved notes and important information."),
        ("✅", "Tasks & Goals", "Track daily tasks, goals and progress."),
        ("📚", "Learning Hub", "Turn any topic into a simple learning plan."),
    ]
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(
                f'<div class="feature"><div class="icon">{icon}</div>'
                f'<h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True
            )
        if i in (2, 5):
            st.write("")

# ---------- Chat ----------
elif page == "💬 AI Chat":
    st.title("💬 AI Chat Assistant")
    st.caption("Ask LifeMind anything about learning, planning, writing, or everyday knowledge.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("Ask your personal AI assistant...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        answer = ask_ai(
            prompt,
            "You are LifeMind AI, a helpful personal knowledge and productivity assistant. "
            "Be clear, practical, friendly, and concise. Never pretend to remember information "
            "that the user has not provided."
        )
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

# ---------- Notes ----------
elif page == "📝 Notes":
    st.title("📝 Personal Notes")
    st.caption("Capture and organize your knowledge.")

    with st.form("note_form", clear_on_submit=True):
        title = st.text_input("Note title")
        category = st.selectbox("Category", ["General", "Ideas", "Study", "Work", "Personal", "Projects"])
        content = st.text_area("Write your note", height=180)
        save = st.form_submit_button("💾 Save Note", type="primary")
        if save and title.strip() and content.strip():
            conn.execute(
                "INSERT INTO notes(title,content,category,created_at) VALUES(?,?,?,?)",
                (title, content, category, datetime.now().isoformat(timespec="seconds"))
            )
            conn.commit()
            st.success("Note saved successfully.")

    st.divider()
    search = st.text_input("🔎 Search notes")
    rows = conn.execute(
        "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY id DESC",
        (f"%{search}%", f"%{search}%")
    ).fetchall()

    for r in rows:
        with st.expander(f"{r['title']}  •  {r['category']}"):
            st.write(r["content"])
            st.caption(f"Created: {r['created_at']}")

# ---------- Documents ----------
elif page == "📄 Documents":
    st.title("📄 Document Intelligence")
    st.caption("Upload a document, extract its text, summarize it, or ask questions.")

    uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])
    if uploaded:
        text = ""
        if uploaded.type == "application/pdf":
            if PdfReader is None:
                st.error("PDF support requires pypdf. Add it to requirements.txt.")
            else:
                reader = PdfReader(uploaded)
                text = "\n".join((p.extract_text() or "") for p in reader.pages)
        else:
            text = uploaded.read().decode("utf-8", errors="ignore")

        st.session_state["document_text"] = text
        st.success(f"Loaded {uploaded.name}.")

    text = st.session_state.get("document_text", "")
    if text:
        st.info(f"Document text loaded: {len(text):,} characters.")
        tab1, tab2 = st.tabs(["✨ Summarize", "❓ Ask Questions"])

        with tab1:
            if st.button("Generate AI Summary", type="primary"):
                st.write(ask_ai(
                    "Summarize the following document in clear bullet points. "
                    "Highlight key ideas, important facts, decisions, and action items.\n\n"
                    + text[:30000]
                ))

        with tab2:
            q = st.text_input("Ask a question about this document")
            if st.button("Ask Document"):
                if q:
                    st.write(ask_ai(
                        f"Answer only from the document below. If the answer is not present, say so.\n\n"
                        f"QUESTION: {q}\n\nDOCUMENT:\n{text[:30000]}"
                    ))

# ---------- Tasks ----------
elif page == "✅ Tasks & Goals":
    st.title("✅ Tasks & Goals")
    st.caption("Keep your day focused and measurable.")

    with st.form("task_form", clear_on_submit=True):
        task = st.text_input("Task or goal")
        due = st.date_input("Due date", value=date.today())
        add = st.form_submit_button("➕ Add Task", type="primary")
        if add and task.strip():
            conn.execute(
                "INSERT INTO tasks(task,due_date) VALUES(?,?)",
                (task, str(due))
            )
            conn.commit()

    rows = conn.execute("SELECT * FROM tasks ORDER BY completed, due_date, id DESC").fetchall()
    for r in rows:
        checked = st.checkbox(
            f"{r['task']}  —  {r['due_date'] or 'No date'}",
            value=bool(r["completed"]),
            key=f"task_{r['id']}"
        )
        if checked != bool(r["completed"]):
            conn.execute("UPDATE tasks SET completed=? WHERE id=?", (int(checked), r["id"]))
            conn.commit()

# ---------- Important Dates ----------
elif page == "📅 Important Dates":
    st.title("📅 Important Dates")
    st.caption("Keep birthdays, deadlines, events and milestones in one place.")

    with st.form("date_form", clear_on_submit=True):
        title = st.text_input("Event title")
        event_date = st.date_input("Date", value=date.today())
        notes = st.text_area("Notes", height=100)
        add = st.form_submit_button("📌 Save Date", type="primary")
        if add and title.strip():
            conn.execute(
                "INSERT INTO dates(title,event_date,notes) VALUES(?,?,?)",
                (title, str(event_date), notes)
            )
            conn.commit()
            st.success("Important date saved.")

    rows = conn.execute("SELECT * FROM dates ORDER BY event_date").fetchall()
    for r in rows:
        st.markdown(
            f"**{r['title']}**  \n"
            f"📅 {r['event_date']}  \n"
            f"{r['notes']}"
        )
        st.divider()

# ---------- Learning ----------
elif page == "📚 Learning":
    st.title("📚 Learning Hub")
    st.caption("Create a simple AI-powered learning path for any topic.")

    topic = st.text_input("What do you want to learn?")
    level = st.selectbox("Your level", ["Beginner", "Intermediate", "Advanced"])
    if st.button("✨ Create Learning Plan", type="primary"):
        if topic.strip():
            result = ask_ai(
                f"Create a practical learning roadmap for {topic}. Level: {level}. "
                "Include concepts in order, mini projects, practice tasks, and a 7-day starter plan."
            )
            st.markdown(result)

# ---------- Dashboard ----------
elif page == "📊 Dashboard":
    st.title("📊 Personal Dashboard")
    notes_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    tasks_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE completed=1").fetchone()[0]
    dates_count = conn.execute("SELECT COUNT(*) FROM dates").fetchone()[0]

    c1, c2, c3, c4 = st.columns(4)
    for c, label, value in [
        (c1, "Notes", notes_count),
        (c2, "Tasks", tasks_count),
        (c3, "Completed", completed),
        (c4, "Important Dates", dates_count),
    ]:
        with c:
            st.markdown(
                f'<div class="metric"><div class="small">{label}</div><b>{value}</b></div>',
                unsafe_allow_html=True
            )

    st.write("")
    progress = (completed / tasks_count) if tasks_count else 0
    st.subheader("Task Progress")
    st.progress(progress)
    st.caption(f"{completed} of {tasks_count} tasks completed.")

    st.subheader("Quick Overview")
    latest_notes = conn.execute("SELECT title, category FROM notes ORDER BY id DESC LIMIT 5").fetchall()
    if latest_notes:
        for n in latest_notes:
            st.write(f"📝 **{n['title']}** — {n['category']}")
    else:
        st.info("No notes yet. Add your first note from the Notes workspace.")

st.markdown("---")
st.caption("LifeMind AI • Personal Life & Knowledge Assistant")
