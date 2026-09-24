# ==============================================================================
# Step 1: Import Libraries
# ==============================================================================
import os
import sqlite3
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# ==============================================================================
# Step 2: Page Configuration
# ==============================================================================
# Must be the first Streamlit command executed
st.set_page_config(
    page_title="AI Chatbot",
    layout="wide",
)

# ==============================================================================
# Step 3: Load Environment Variables & Configure Gemini API
# ==============================================================================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ==============================================================================
# Step 4: Database Functions (SQLite - Persistent Storage)
# ==============================================================================
DB_NAME = "chat_history.db"

def init_db():
    """Initializes the database and creates the messages table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_message(role, content):
    """Saves a single message to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (role, content) VALUES (?, ?)",
        (role, content)
    )
    conn.commit()
    conn.close()

def load_messages():
    """Loads all user and assistant messages in ascending order by timestamp."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT role, content FROM messages ORDER BY timestamp ASC"
    )
    rows = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

def clear_db_history():
    """Deletes all messages from the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM messages")
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

# ==============================================================================
# Step 5: System Prompts (Chatbot Tones)
# ==============================================================================
TONE_PROMPTS = {
    "Default": "You are a helpful AI assistant.",
    "Friendly": "You are a friendly and cheerful assistant. Always be encouraging and supportive. Use simple language and a positive attitude.",
    "Humorous": "You are a witty assistant. Add light humor where appropriate. Keep answers informative and friendly.",
    "Unfriendly": "You are an unfriendly assistant. Always don't be encouraging and supportive. Use simple language and a negative attitude.",
    "Hindi Language": "You are a helpful assistant. Answer only in Hindi. Use simple and clear language.",
    "Professional": "You are a highly professional corporate assistant. Provide concise, objective, and well-structured answers without fluff.",
    "Sarcastic": "You are a highly sarcastic assistant. Answer questions accurately but with a thick layer of sarcasm and dry wit.",
    "Pirate": "You are a swashbuckling pirate captain. Answer all questions using pirate slang, nautical terms, and an adventurous tone.",
    "Academic": "You are an academic scholar. Provide highly detailed, analytical, and well-researched answers using formal vocabulary."
}

# ==============================================================================
# Step 6: Sidebar Settings & Controls
# ==============================================================================
with st.sidebar:
    st.title("Settings")

    # --- API Key Status ---
    if GEMINI_API_KEY:
        st.success("Gemini API Key loaded from .env")
    else:
        st.error("GEMINI_API_KEY not found in .env file")
    
    st.divider()

    model = st.selectbox(
        "Choose Model",
        [
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",   
        ],
    )

    st.divider()
    
    # --- Tone Selection ---
    selected_tones = st.multiselect(
        "Choose Tone(s)",
        list(TONE_PROMPTS.keys()),
        default=["Default"],
        help="You can select multiple tones to combine them!"
    )

    # --- Custom System Prompt Input ---
    custom_system_prompt = st.text_area(
        "Custom System Prompt",
        placeholder="Type any additional instructions for the AI here...",
    )

    st.divider()

    # --- Direct Document Upload (Passed directly to Gemini without extraction) ---
    st.subheader("Upload Document (PDF / TXT)")
    uploaded_file = st.file_uploader(
        "Upload a PDF or TXT file",
        type=["pdf", "txt"]
    )
    
    if uploaded_file is not None:
        st.success(f"File `{uploaded_file.name}` ready to send directly to LLM!")

    st.divider()

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.5,
        value=0.7,
        step=0.1,
    )

    if st.button("Clear Chat"):
        clear_db_history()
        st.session_state.messages = []
        st.rerun()

# ==============================================================================
# Step 7: Build the Final System Prompt
# ==============================================================================
active_prompts = []

for tone in selected_tones:
    active_prompts.append(TONE_PROMPTS[tone])

if custom_system_prompt.strip():
    active_prompts.append(f"Additional Instructions from user:\n{custom_system_prompt.strip()}")

if uploaded_file is not None:
    active_prompts.append(
        "A document has been attached to the conversation. Prioritize information from this document when answering."
    )

combined_system_prompt = "\n\n".join(active_prompts)
if not combined_system_prompt:
    combined_system_prompt = "You are a helpful AI assistant."

# ==============================================================================
# Step 8: Main UI Header
# ==============================================================================
st.title("AI Chatbot")
st.caption("Powered by Google Gemini API (Multimodal) | Chat History saved to SQLite")

if not GEMINI_API_KEY:
    st.warning("Please add your GEMINI_API_KEY to the .env file to start chatting.")

with st.expander("View Current System Prompt & Instructions"):
    st.text(combined_system_prompt)

# ==============================================================================
# Step 9: Load & Display Chat History
# ==============================================================================
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    # Load past messages from database in ascending order
    db_history = load_messages()
    
    # Initialize session state with the system prompt followed by DB history
    st.session_state.messages = [
        {"role": "system", "content": combined_system_prompt}
    ] + db_history
else:
    # Update the system prompt dynamically if settings change
    if st.session_state.messages[0]["role"] == "system":
        st.session_state.messages[0]["content"] = combined_system_prompt

# Display all messages in ascending chronological order
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ==============================================================================
# Step 10: Handle User Input & Direct Multimodal LLM Streaming
# ==============================================================================
# The chat input is disabled if no API key is provided
prompt = st.chat_input("Type your message...", disabled=not GEMINI_API_KEY)

if prompt and GEMINI_API_KEY:
    # Initialize Gemini model
    gemini_model = genai.GenerativeModel(
        model_name=model,
        system_instruction=combined_system_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
        ),
    )

    # 1. Save User Message to Session State & DB
    display_user_text = f"📎 *[Attached: {uploaded_file.name}]*\n\n{prompt}" if uploaded_file else prompt
    st.session_state.messages.append({"role": "user", "content": display_user_text})
    save_message("user", display_user_text)

    # 2. Display user message
    with st.chat_message("user"):
        st.markdown(display_user_text)

    # 3. Build Gemini chat history (exclude system messages)
    gemini_history = []
    for msg in st.session_state.messages[:-1]:  # exclude the latest user message
        if msg["role"] == "system":
            continue
        gemini_role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": gemini_role, "parts": [msg["content"]]})

    # 4. Prepare message content: pass file directly to Gemini if attached
    if uploaded_file is not None:
        file_mime = uploaded_file.type or ("application/pdf" if uploaded_file.name.endswith(".pdf") else "text/plain")
        file_part = {
            "mime_type": file_mime,
            "data": uploaded_file.getvalue()
        }
        message_to_send = [file_part, prompt]
    else:
        message_to_send = prompt

    # 5. Generate and Display Assistant Response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            chat = gemini_model.start_chat(history=gemini_history)
            response = chat.send_message(message_to_send, stream=True)

            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

            # 6. Save Assistant Message to Session State & DB
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_message("assistant", full_response)

        except Exception as e:
            st.error(f"Error: {e}")