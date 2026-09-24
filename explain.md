# AI Chatbot - Line-by-Line Code Explanation

This document explains every part of [`app.py`](file:///d:/IIITA_STUF/gen%20ai/AI_Rag_Based_Chat_bot/app.py) in simple, beginner-friendly terms.

---

## Direct File Processing (Why We Don't Need PyPDF2)

### Is it possible to give files directly to the LLM?
**Yes, 100% possible!** Google Gemini models (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`, etc.) are **natively multimodal**. 

They don't just read plain text; they can directly read and understand:
- **PDF files** (including tables, multi-column layouts, charts, and images inside the PDF)
- **Text files** (`.txt`, `.py`, `.csv`, etc.)

### Why this is much better and simpler:
1. **No External Libraries**: No need for `PyPDF2` (which often crashes on scanned PDFs, encrypted files, or complex layouts).
2. **No Text Truncation**: Gemini can ingest hundreds of pages directly with its huge context window (over 1,000,000 tokens).
3. **Simpler Code**: Removed the messy file-reading logic and character cutting. We simply hand the file's raw bytes to Gemini as a dictionary part:
   ```python
   file_part = {
       "mime_type": uploaded_file.type,  # e.g., 'application/pdf'
       "data": uploaded_file.getvalue()  # raw bytes of the file
   }
   ```

---

## Technologies Used

| Technology | Why We Use It |
|---|---|
| **Streamlit** | To create the web page interface |
| **Google Gemini API** | Multimodal LLM that directly reads text, PDFs, and prompts |
| **SQLite** | A simple local database to save chat history |
| **python-dotenv** | To safely load the API key from a `.env` file |

---

## Step-by-Step Code Walkthrough (Ascending Order)

### Step 1: Import Libraries
```python
import os
import sqlite3
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
```
Imports only the essential modules. Notice that `PyPDF2` and `uuid` are completely gone.

---

### Step 2: Page Configuration
```python
st.set_page_config(
    page_title="AI Chatbot",
    layout="wide",
)
```
Configures the browser tab title and wide layout. Must be executed first in Streamlit.

---

### Step 3: Load Environment Variables & Configure Gemini API
```python
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
```
Loads your secret `GEMINI_API_KEY` from `.env` and initializes the Google GenAI SDK.

---

### Step 4: Database Functions (SQLite - Persistent Storage)
Four simple functions save and load messages from `chat_history.db`:
- `init_db()`: Creates the `messages` table (`id`, `role`, `content`, `timestamp`).
- `save_message(role, content)`: Inserts a new chat message into SQLite.
- `load_messages()`: Fetches all messages sorted in ascending chronological order (`ORDER BY timestamp ASC`).
- `clear_db_history()`: Wipes all messages when the user clicks "Clear Chat".

---

### Step 5: System Prompts (Chatbot Tones)
`TONE_PROMPTS` defines different personality instructions (Default, Friendly, Humorous, Hindi Language, Professional, Sarcastic, Pirate, Academic).

---

### Step 6: Sidebar Settings & Controls
The sidebar on the left lets users:
- Verify API key status
- Select a Gemini model (`gemini-2.5-flash`, `gemini-2.0-flash`, etc.)
- Select tones & add custom instructions
- **Upload a PDF or TXT file**: Kept in memory to be passed directly to the model
- Adjust creativity via the temperature slider
- Click "Clear Chat" to reset history

---

### Step 7: Build the Final System Prompt
Merges selected tones and custom instructions into a single system instruction for Gemini.

---

### Step 8: Main UI Header
Renders the page title, subtitle, API key warning (if not found), and an expander to view the active prompt.

---

### Step 9: Load & Display Chat History
Loads stored messages from the SQLite database into `st.session_state.messages` and displays each chat bubble in chronological order.

---

### Step 10: Handle User Input & Direct Multimodal LLM Streaming
When the user submits a message:
1. **Prepare Message Content**:
   If a document is uploaded, we wrap its raw bytes and MIME type into a part dictionary:
   ```python
   file_part = {
       "mime_type": file_mime,
       "data": uploaded_file.getvalue()
   }
   message_to_send = [file_part, prompt]
   ```
2. **Send to Gemini**:
   Calls `chat.send_message(message_to_send, stream=True)`. Gemini receives both the raw file and the user question at once.
3. **Stream Response**:
   Streams the tokens in real time with a cursor effect (`▌`).
4. **Save to History & SQLite**:
   Both user and assistant responses are persisted for reload.

---

## How to Run

1. Ensure `.env` contains your key:
   ```bash
   GEMINI_API_KEY="your_api_key_here"
   ```
2. Install the streamlined requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Streamlit:
   ```bash
   streamlit run app.py
   ```
