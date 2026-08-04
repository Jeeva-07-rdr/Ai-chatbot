# UMI AI Chatbot — Comprehensive Technical Documentation & Architecture Reference

**Document Version**: 2.0.0  
**Last Updated**: August 4, 2026  
**System Architecture**: Enterprise Django 6.0 Backend with MySQL (MariaDB) Database, Vanilla Modern Glassmorphism UI, LlamaIndex RAG Engine, Dual LLM Providers (Ollama & Gemini), and Enterprise Authentication & Security Subsystems.

---

## 1. System Overview & Core Capabilities

UMI AI Chatbot is an enterprise-grade AI assistant application designed for low-latency multi-turn conversations, document context extraction (RAG), and account management.

### Key Capabilities:
- **Dual AI Providers**: Support for local LLMs via Ollama (`qwen2.5:0.5b`, `llama3.2:latest`, `deepseek-r1:7b`) and cloud-hosted LLMs via Google Gemini API (`gemini-2.5-flash`, `gemini-2.5-pro`).
- **Enterprise MySQL Architecture**: Persistent storage using MySQL/MariaDB database (`umi_chatbot_db`).
- **Authentication & Security Subsystem**: User Registration, Login, Logout, Remember Me (30-day session), Password Recovery & Reset via SMTP, Rate Limiting, Anti-Enumeration, and Anti-Caching headers.
- **LlamaIndex RAG Integration**: Page-aware document extraction and chunking using LlamaIndex `SentenceSplitter` and `LlamaDocument` parsers across 25+ document and code file extensions.
- **Profile & Avatar Management**: Custom username, email, name, and profile picture upload/resize/removal using Pillow (`LANCZOS` 300x300 optimization).
- **Atomic Account Cleanup**: Transactional cascading deletion of user account, chat sessions, message history, uploaded documents, memory records, and disk files.

---

## 2. Technology Stack

| Layer | Technology / Package | Function |
| :--- | :--- | :--- |
| **Framework** | Python 3.13 / Django 6.0.6 | Core Web Backend, ORM, Views, Middleware |
| **Database** | MySQL / MariaDB (via PyMySQL) | Relational Database Engine (`umi_chatbot_db`) |
| **Frontend** | HTML5, Vanilla JavaScript, Vanilla CSS | Responsive Glassmorphic Dark/Light UI |
| **RAG / Vectoring** | LlamaIndex (`llama-index-core`, `llama-index-readers-file`) | Document Chunking, Node Parsing & Vector Search |
| **LLM Integrations** | `google-genai` (v2.10.0), Ollama REST API | Gemini & Ollama Inference Drivers |
| **Image Processing**| Pillow (v12.3.0) | Avatar Upload Optimization & Resizing |
| **Email Subsystem** | Django SMTP + `EmailMultiAlternatives` | HTML Password Reset Email Delivery |
| **Profiling / Audit**| Custom `PerformanceTracer` & `RequestLoggingMiddleware` | Microsecond Timing & MySQL Log Persistence |

---

## 3. Comprehensive Record of All Changes Made

### 3.1 MySQL Database Connection & Schema Migration
- **PyMySQL Integration**: Injected PyMySQL compatibility patch in `umi_project/settings.py` for MariaDB/MySQL (`check_database_version_supported` and bulk insert overrides).
- **Database Schema (`create_clean_schema.py`)**: Created 14 structured tables:
  1. `users`: Built-in Django user table mapping (`User._meta.db_table = 'users'`).
  2. `user_profiles`: Avatar, role, bio, and account status.
  3. `user_settings`: Theme, default AI provider, model name, streaming mode, response style.
  4. `ai_preferences`: Fine-grained temperature and token limits.
  5. `chat_sessions`: Conversations with UUID primary keys (`Conversation`).
  6. `messages`: User and AI message content linked to session ID (`Message`).
  7. `conversation_memory`: Summarized long-context conversation history.
  8. `documents`: File attachments, size, path, and MIME type (`Attachment`).
  9. `auth_sessions`: Active user login session tracking.
  10. `analytics`: Aggregate throughput and latency metrics.
  11. `runtime_logs`: High-precision system logs (`LogEntry._meta.db_table = 'runtime_logs'`).
  12. `auth_user_groups`: Django permissions junction table.
  13. `auth_user_user_permissions`: Django user permissions junction table.
  14. `password_reset_tokens`: Password reset single-use token table.

### 3.2 Enterprise Authentication & Middleware (`chat/middleware.py`)
- **Login Required Middleware (`EnterpriseAuthMiddleware`)**:
  - Automatically intercepts all requests to private endpoints (`/`, `/chat/*`, `/settings/*`, `/help/*`).
  - Redirects unauthenticated users to `/login/?next=<path>`.
  - Exempts public authentication routes (`/login/`, `/register/`, `/forgot-password/`, `/reset-password/`, `/static/`, `/media/`).
  - Injects anti-caching HTTP headers (`Cache-Control: no-cache, no-store, must-revalidate, max-age=0`, `Pragma: no-cache`, `Expires: 0`) to prevent browser back-button access post-logout.

### 3.3 Enterprise Password Reset System
- **Database Model (`PasswordResetToken` in `chat/models.py`)**:
  - Stores single-use tokens, user FK, 30-minute expiration timestamp (`expires_at`), and `is_used` status.
- **Anti-Enumeration Protection**:
  - `/forgot-password/` accepts Email Address OR Username and returns a standard security message: *"If an account matching this input exists, a password reset link has been sent to the registered email address."*
- **Rate Limiting**:
  - Enforced via Django Cache (maximum 3 requests per 15 minutes per IP/input).
- **Responsive HTML Email Template (`templates/emails/password_reset_email.html`)**:
  - Features UMI logo header badge, gradient banner, personalized greeting, Reset Password button, text link fallback, 30-min expiry notice, and support contact footer.
- **SMTP Configuration**:
  - Configured Gmail SMTP (`smtp.gmail.com:587`, TLS enabled, App Password `afcjlcrivsjqakpo`).
  - Includes step-by-step diagnostic logging (`========== PASSWORD RESET ==========`) and fallback handling.
- **Reset Execution & Session Invalidation (`reset_password_view`)**:
  - Validates token freshness and unused state, updates password using Django PBKDF2 hashing, marks token `is_used=True`, invalidates all active user sessions across browsers, and redirects to `/login/`.

### 3.4 Profile Management & Avatar Processing
- **Profile Settings View (`save_profile` in `chat/views.py`)**:
  - Updates Username, Email Address, First Name, and Last Name in MySQL.
- **Avatar Image Optimization (`optimize_profile_picture` in `chat/services.py`)**:
  - Processes uploaded profile pictures using Pillow (`LANCZOS` thumbnail filter to 300x300 JPG format).
- **Avatar Removal (`remove_avatar_view` in `chat/views.py`)**:
  - Deletes avatar image file from disk and resets `profile_pic` field.
- **Dynamic UI Rendering**:
  - Header and Sidebar User Cards display uploaded profile picture or capitalized user initials (`user.first_name|slice:":1"` + `user.last_name|slice:":1"`).

### 3.5 Atomic Account Deletion (Danger Zone)
- **Password Verification Modal (`templates/settings.html`)**:
  - Requires user to confirm password in a Bootstrap modal before account deletion.
- **Atomic Cascade Cleanup (`delete_account` in `chat/views.py`)**:
  - Executes inside `@transaction.atomic`: removes user attachment files and profile picture from disk, deletes user conversations, messages, attachments, memory, user settings, user profile, and user account.

### 3.6 LlamaIndex RAG Integration & Attachment Context
- **SentenceSplitter Node Parser (`chat/rag_service.py`)**:
  - Integrated `llama-index-core` `LlamaDocument` and `SentenceSplitter` parser to chunk uploaded files into context nodes.
- **Multi-Turn Attachment Link Fix**:
  - Restored attachment database linking in `send_message` (`Attachment.objects.filter(id__in=attachment_ids).update(...)`), enabling PDF and document explanations in multi-turn chat sessions.
- **Expanded File Upload Extension Support**:
  - Added support for `.pdf`, `.docx`, `.txt`, `.csv`, `.xlsx`, `.pptx`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.md`, `.py`, `.js`, `.json`, `.html`, `.css`, `.c`, `.cpp`, `.java`, `.go`, `.rs`, `.sql`, `.sh`, `.xml`, `.yaml`, `.yml`.

### 3.7 Navigation & Bug Fixes
- **Notification Bell Removal**: Removed Notification Bell icon and red badge from `templates/header.html`.
- **Global New Chat Button Navigation**: Converted `.new-chat-btn` in `templates/sidebar.html` to an explicit `<a href="{% url 'new_chat' %}">` link and added a global listener in `static/js/sidebar.js`. Fixes "New Chat button not working on Settings/Help pages".
- **Authenticated User Scope Fix**: Updated `delete_chat`, `rename_chat`, `pin_chat`, `archive_chat`, `duplicate_chat`, `reorder_pins`, `search_chats`, `export_chat`, `clear_history`, and `help_view` in `chat/views.py` to resolve `request.user` dynamically, resolving 404 errors during chat management.

---

## 4. Database Schema Structure

```
+---------------------------+-------------------------------------------------------------+
| Table Name                | Primary Purpose                                             |
+---------------------------+-------------------------------------------------------------+
| users                     | Core user account table (username, email, hashed password)  |
| user_profiles             | User profile details (bio, avatar, role, status)           |
| user_settings             | User settings (theme, provider, model, style, profile_pic)  |
| ai_preferences            | AI parameters (temperature, max_tokens)                     |
| chat_sessions             | Conversation metadata (UUID, title, is_pinned, is_archived) |
| messages                  | Individual messages (sender, content, timestamp)            |
| conversation_memory       | Summarized conversation memory                              |
| documents                 | Uploaded attachments (file_name, file_size, path, type)     |
| auth_sessions             | User login session tracking                                 |
| analytics                 | Application metrics (request count, response time)          |
| runtime_logs              | System logs and exception tracebacks                        |
| password_reset_tokens     | Cryptographically secure password reset tokens              |
| auth_user_groups          | Django user groups permissions junction table               |
| auth_user_user_permissions| Django user permissions junction table                      |
+---------------------------+-------------------------------------------------------------+
```

---

## 5. Security & Verification Summary

- **Password Hashing**: Django PBKDF2 Password Hashing (`django.contrib.auth.hashers`).
- **CSRF Protection**: All POST forms enforce `{% csrf_token %}` validation.
- **Anti-Caching Header Enforcement**: Authenticated responses send `Cache-Control: no-cache, no-store, must-revalidate` to block back-button access post-logout.
- **System Check Status**: `python manage.py check` — **0 issues identified**.
