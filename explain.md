# AI  Chatbot - Line-by-Line Code Explanation

This document explains every part of `app.py` in simple words so anyone can understand how the chatbot works.

---

## What Does This App Do?

- It's a **chatbot** that runs in your browser (using Streamlit)
- It uses **Google Gemini AI** to answer questions
- You can **upload a PDF or TXT file** and ask questions about it (this is called **RAG** - Retrieval Augmented Generation)
- You can choose the **tone** of the chatbot (Friendly, Sarcastic, Professional, etc.)
- All chat messages are **saved in a local database** (SQLite) so you don't lose them

---

## Technologies Used

| Technology | Why We Use It |
|---|---|
| **Streamlit** | To create the web page (UI) without writing HTML/CSS |
| **Google Gemini API** | The AI brain that generates responses |
| **SQLite** | A simple file-based database to save chat history |
| **PyPDF2** | To read text from PDF files |
| **python-dotenv** | To safely load the API key from a `.env` file |

---

## Step-by-Step Explanation

### Step 1: Import Libraries (Lines 12-18)

```python
import streamlit as st                    # For building the web UI
import google.generativeai as genai       # Google Gemini AI SDK
import os                                 # To read environment variables
import PyPDF2                             # To read PDF files
import sqlite3                            # To save chat history locally
import uuid                               # To create unique session IDs
from dotenv import load_dotenv            # To load API key from .env file
```

**What's happening?** We're importing all the tools (libraries) we need.

- `streamlit` → Makes the web page (buttons, text boxes, chat bubbles)
- `google.generativeai` → Connects to Google's Gemini AI
- `os` → Reads values from the `.env` file
- `PyPDF2` → Opens and reads PDF files
- `sqlite3` → Creates and manages a local database
- `uuid` → Generates random unique IDs (like `a1b2c3d4-...`)
- `load_dotenv` → Loads the `.env` file so `os.getenv()` can find our API key

---

### Step 2: Load the API Key (Lines 21-24)

```python
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
```

**What's happening?**

1. `load_dotenv()` → Reads the `.env` file and loads all key-value pairs into the system
2. `os.getenv("GEMINI_API_KEY")` → Gets the value of `GEMINI_API_KEY` from the `.env` file
3. `if GEMINI_API_KEY:` → If the key exists (is not empty/None)...
4. `genai.configure(...)` → ...tell the Gemini SDK to use this key for all future API calls

> **Simple analogy:** This is like entering your password before you can use the AI service.

---

### Step 3: Database Functions (Lines 29-74)

We have 4 simple functions to manage chat history:

#### 3a. `init_db()` - Create the database table

```python
DB_NAME = "chat_history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
```

**What's happening?**
- Opens (or creates) a file called `chat_history.db`
- Creates a table called `messages` with these columns:
  - `id` → Auto-incrementing number (1, 2, 3...)
  - `session_id` → Which chat session this message belongs to
  - `role` → Who sent it: "user" or "assistant"
  - `content` → The actual message text
  - `timestamp` → When the message was sent
- `CREATE TABLE IF NOT EXISTS` → Only creates the table if it doesn't already exist (safe to run many times)

#### 3b. `save_message()` - Save a message

```python
def save_message(session_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()
```

**What's happening?**
- Opens the database, inserts one new row with the session ID, role, and message content
- The `?` marks are placeholders that get filled with actual values (this prevents SQL injection)

#### 3c. `load_messages()` - Load past messages

```python
def load_messages(session_id):
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in rows]
```

**What's happening?**
- Fetches all messages for a given session, sorted by time (oldest first)
- Returns them as a list of dictionaries like: `[{"role": "user", "content": "Hi"}, ...]`

#### 3d. `clear_history()` - Delete chat history

```python
def clear_history(session_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    conn.commit()
    conn.close()
```

**What's happening?** Deletes all messages for this session from the database.

#### Initialize the database:

```python
init_db()
```

This runs `init_db()` once when the app starts to make sure the table exists.

---

### Step 4: Define Chatbot Tones (Lines 79-89)

```python
TONES = {
    "Default": "You are a helpful AI assistant.",
    "Friendly": "You are a friendly and cheerful assistant...",
    "Sarcastic": "You are a sarcastic assistant...",
    ...
}
```

**What's happening?**
- This is a **dictionary** (key-value pairs) that maps tone names to instructions for the AI
- When the user picks "Sarcastic", we send the sarcastic instruction to Gemini so it responds with sarcasm
- These instructions are called **system prompts** - they tell the AI how to behave

---

### Step 5: File Reader Function (Lines 94-108)

```python
def read_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.type == "text/plain":
            text = uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Error reading file: {e}")
    return text
```

**What's happening?**
1. Check the file type
2. If it's a **TXT file** → just read it as text
3. If it's a **PDF file** → use PyPDF2 to go through each page and extract the text
4. If anything goes wrong → show an error message
5. Return all the extracted text

> **This is the "R" in RAG** - we *retrieve* text from the document so the AI can use it.

---

### Step 6: Page Setup (Lines 113-117)

```python
st.set_page_config(page_title="AI Chatbot", layout="wide")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
```

**What's happening?**
- `set_page_config` → Sets the browser tab title to "AI Chatbot" and uses full screen width
- `session_state` → Streamlit's way of remembering data between page refreshes
- `uuid.uuid4()` → Creates a random unique ID like `7ec4556f-...` for this chat session
- We only create a new ID if one doesn't exist yet (so refreshing the page keeps the same session)

---

### Step 7: Sidebar - All Settings (Lines 122-176)

```python
with st.sidebar:
    st.title("Settings")
```

**What's happening?** Everything inside `with st.sidebar:` appears on the left panel.

The sidebar contains:
- **API Key status** → Shows green if key is loaded, red if missing
- **Model selector** → Dropdown to pick which Gemini model to use
- **Tone picker** → Multi-select to choose one or more tones
- **Custom prompt** → Text box for extra instructions
- **File uploader** → Drag & drop PDF/TXT files (the RAG feature)
- **Temperature slider** → Controls creativity (0 = factual, 1.5 = very creative)
- **Clear Chat button** → Deletes all history and starts fresh

#### Important detail - File upload:
```python
if len(doc_text) > 40000:
    doc_text = doc_text[:40000] + "\n\n...[TEXT CUT SHORT - FILE TOO LONG]..."
```
We limit document text to 40,000 characters because the AI has a maximum input size.

---

### Step 8: Build the System Prompt (Lines 182-199)

```python
parts = []

for tone in selected_tones:
    parts.append(TONES[tone])

if custom_prompt.strip():
    parts.append(f"Additional Instructions:\n{custom_prompt.strip()}")

if doc_text.strip():
    parts.append("--- DOCUMENT CONTEXT ---\n..." + doc_text + "...")

system_prompt = "\n\n".join(parts) if parts else "You are a helpful AI assistant."
```

**What's happening?**
1. Create an empty list called `parts`
2. Add the text for each selected tone
3. If the user typed a custom prompt, add that too
4. If a document was uploaded, add the document text with instructions to use it
5. Join all parts together with blank lines between them → this becomes the final system prompt

> **Simple analogy:** Think of this as writing a job description for the AI. "Be friendly + speak Hindi + use this document to answer questions."

---

### Step 9: Main Chat Area (Lines 204-212)

```python
st.title("AI Chatbot")
st.caption("Powered by Google Gemini API | Chat History saved to SQLite")

if not GEMINI_API_KEY:
    st.warning("Please add your GEMINI_API_KEY to the .env file to start chatting.")

with st.expander("View Current System Prompt & Context"):
    st.text(system_prompt)
```

**What's happening?**
- Shows the title and subtitle on the main page
- If no API key is found → shows a yellow warning
- The expander lets users click to see what instructions the AI is currently following

---

### Step 10: Load & Display Chat History (Lines 217-229)

```python
if "messages" not in st.session_state or not st.session_state.messages:
    past_messages = load_messages(st.session_state.session_id)
    st.session_state.messages = [{"role": "system", "content": system_prompt}] + past_messages
else:
    st.session_state.messages[0] = {"role": "system", "content": system_prompt}
```

**What's happening?**
- **First visit:** Load old messages from the database and put them in session state
- **Return visit:** Just update the system prompt (in case the user changed tone/settings)
- The messages list looks like: `[system_prompt, user_msg_1, assistant_msg_1, user_msg_2, ...]`

```python
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
```

- Loop through all messages and show them as chat bubbles
- Skip the system prompt (it's invisible to the user)
- `st.chat_message("user")` shows a human icon, `st.chat_message("assistant")` shows an AI icon

---

### Step 11: Handle New Messages (Lines 235-283)

This is the **core logic** - what happens when the user sends a message:

#### A) Set up the Gemini model

```python
gemini_model = genai.GenerativeModel(
    model_name=model,
    system_instruction=system_prompt,
    generation_config=genai.types.GenerationConfig(temperature=temperature),
)
```

- Creates a Gemini model instance with the selected model, system prompt, and temperature

#### B) Save and show the user's message

```python
st.session_state.messages.append({"role": "user", "content": user_input})
save_message(st.session_state.session_id, "user", user_input)
with st.chat_message("user"):
    st.markdown(user_input)
```

- Add the message to session state (for display)
- Save it to the database (for persistence)
- Show it on screen as a chat bubble

#### C) Convert history to Gemini's format

```python
history = []
for msg in st.session_state.messages[:-1]:
    if msg["role"] == "system":
        continue
    role = "user" if msg["role"] == "user" else "model"
    history.append({"role": role, "parts": [msg["content"]]})
```

**Why is this needed?**
- Our app stores messages as: `{"role": "assistant", "content": "Hello"}`
- Gemini expects them as: `{"role": "model", "parts": ["Hello"]}`
- So we convert "assistant" → "model" and "content" → "parts"
- We skip system messages because the system prompt is passed separately

#### D) Stream the AI response

```python
chat = gemini_model.start_chat(history=history)
response = chat.send_message(user_input, stream=True)

for chunk in response:
    if chunk.text:
        full_response += chunk.text
        placeholder.markdown(full_response + "▌")

placeholder.markdown(full_response)
```

**What's happening?**
1. `start_chat(history=...)` → Creates a chat session with all the past messages so the AI has context
2. `send_message(user_input, stream=True)` → Sends the user's message and gets the response in small pieces (streaming)
3. The `for` loop receives each piece and adds it to the screen, creating a **typing effect**
4. The `"▌"` character is the blinking cursor that disappears when the response is complete

#### E) Save the AI's response

```python
st.session_state.messages.append({"role": "assistant", "content": full_response})
save_message(st.session_state.session_id, "assistant", full_response)
```

- Save the complete response to both session state and database

---

## How RAG Works in This App

```
1. User uploads a PDF/TXT file
         ↓
2. read_file() extracts all text from the file
         ↓
3. The text is added to the system prompt with instructions:
   "Use this document to answer questions"
         ↓
4. When the user asks a question, Gemini reads the
   document text + question and gives an answer
         ↓
5. The AI prioritizes the document but can also use
   its general knowledge if the answer isn't in the doc
```

> **RAG = Retrieval Augmented Generation**
> - **Retrieval** = We retrieve/extract text from the uploaded document
> - **Augmented** = We augment (add to) the AI's knowledge with this text
> - **Generation** = The AI generates an answer using both the document and its training

---

## File Structure

```
AI_Rag_Based_Chat_bot/
├── app.py              ← Main application code (this file)
├── .env                ← Stores your GEMINI_API_KEY (keep secret!)
├── requirements.txt    ← List of Python packages needed
├── chat_history.db     ← SQLite database (created automatically)
├── explain.md          ← This explanation file
└── .gitignore          ← Tells Git which files to ignore
```

---

## How to Run

1. Add your Gemini API key to `.env`:
   ```
   GEMINI_API_KEY="your_key_here"
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the app:
   ```
   streamlit run app.py
   ```
4. Open `http://localhost:8501` in your browser
