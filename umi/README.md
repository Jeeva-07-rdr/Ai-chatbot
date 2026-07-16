# UMI AI Chatbot 🤖✨

An enterprise-grade, premium assistant web application built with a **Django** backend, **Vanilla CSS/JS** frontend, and integrated with both local **Ollama** and cloud-hosted **Google Gemini** models.

---

## 🌟 Key Features

- **Dual AI Providers**: Support for local models (via Ollama) and cloud models (via Google Gemini 2.5).
- **Progressive Streaming**: Real-time response streaming for a smooth and responsive user experience.
- **Connection Pooling & Caching**: Efficient connection management with persistent sessions and Django local memory cache (`LocMemCache`).
- **File Upload & Parsing**: Supports document analysis for PDF (`pypdf`), Word (`python-docx`), and Excel (`openpyxl`) files.
- **Dynamic Response Styles**: Tailored responses based on styles: *Short*, *Balanced*, *Detailed*, and *Research*.
- **Persona Preservation**: Custom UMI system prompts and identity filters ensure the assistant maintains its unique identity.

---

## 🛠️ Architecture & Tech Stack

- **Backend**: Python, Django 6.0.6
- **Frontend**: HTML5, Vanilla JavaScript, Vanilla CSS (Glassmorphism & Sleek Dark/Light themes)
- **AI Integrations**:
  - `google-genai` (v2.10.0) SDK
  - Local Ollama API (e.g., `llama3.2:latest`, `qwen2.5:0.5b`)
- **Document Extractors**: `pypdf`, `python-docx`, `openpyxl`
- **Output Rendering**: Markdown parsing to HTML elements with code syntax highlighting.

---

## 🚀 Installation & Setup Guide

Follow these steps to run the UMI Chatbot locally:

### 1. Install & Launch Ollama (For Local Models)
1. Download and install [Ollama](https://ollama.com/) for your operating system.
2. Open a terminal and pull the required models:
   ```bash
   ollama pull llama3.2:latest
   ollama pull qwen2.5:0.5b
   ```
3. Start the Ollama server (usually runs automatically, otherwise run `ollama serve`).

### 2. Configure Virtual Environment
1. Navigate to the project root directory and create a python virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

### 3. Install Python Dependencies
Install all required packages:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root folder of the project with your Gemini API key:
```ini
# .env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 5. Run Database Migrations
Apply migrations to setup the local SQLite database:
```bash
python manage.py migrate
```

### 6. Start the Development Server
Launch the Django server:
```bash
python manage.py runserver
```
The application will be accessible at: `http://127.0.0.1:8000/`

---

## 📂 Project Structure

```text
c:/AI_ChatBot/
├── chat/                   # Main application containing views, models, and services
│   ├── ai_service.py       # Core AI service mapping prompts to Gemini & Ollama
│   ├── ollama_service.py   # Ollama API client integration
│   ├── services.py         # Markdown parsing and document text extraction
│   ├── models.py           # Django models (Conversation, Message, UserSettings, etc.)
│   └── views.py            # View controllers for chat messaging and attachments
├── templates/              # HTML layout and template files
├── static/                 # Static assets (CSS styles, JS interaction scripts)
├── requirements.txt        # Python dependency manifest
└── manage.py               # Django CLI management script
```

---

## 🔒 License
This project is proprietary. All rights reserved.
