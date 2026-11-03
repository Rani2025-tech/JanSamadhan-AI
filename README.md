# JanSamadhan - AI Grievance Redressal Portal

JanSamadhan is an AI-powered, multilingual citizen grievance redressal and public administration portal for the State of Odisha. It features an interactive, highly accessible frontend alongside an intelligent FastAPI backend equipped with Gemini AI classification, rule-based multilingual fallback, conversational slot-filling, duplicate detection, and RAG over public policy FAQs.

---

## 🏗️ Architecture Overview

```
JanSamadhan-AI/
├── backend/
│   ├── app/
│   │   ├── config.py           # Environment & JWT settings
│   │   ├── database.py         # SQLAlchemy SQLite session engine
│   │   ├── models.py           # User, Complaint, StatusHistory, Notification, ChatSession, ChatMessage
│   │   ├── schemas.py          # Pydantic validation schemas
│   │   └── routes/
│   │       ├── auth.py         # Mock OTP (123456), JWT tokens, Citizen & Admin auth
│   │       ├── complaints.py   # Complaints CRUD, SLA tracking, feedback, duplicate check
│   │       ├── notifications.py# Real-time citizen updates & platform announcements
│   │       ├── admin.py        # Macro stats, department metrics, hotspot clusters, eval benchmarks
│   │       └── chat.py         # Conversational slot-filling AI assistant endpoint
│   ├── ai/
│   │   ├── gemini_client.py    # Provider-swappable Google Gemini GenAI client
│   │   ├── classifier.py       # High-precision multilingual & Romanized/code-mixed rule-based NLP
│   │   ├── extractor.py        # extract(text) with Pydantic validation & retry fallback
│   │   ├── translator.py       # translate(text, target_lang) for officer remarks
│   │   ├── duplicates.py       # Vector/TF-IDF duplicate detector (same district + category)
│   │   ├── rag.py              # Knowledge Base RAG search engine over markdown FAQs
│   │   └── slot_filler.py      # Conversational slot-filling state machine with confirmation card
│   ├── kb/                     # Department FAQ documentation (PHED, PWD, DISCOM, Municipal, Health, PDS)
│   ├── eval/                   # 65+ labeled multilingual test cases & accuracy benchmark runner
│   ├── seed.py                 # Seeds exact demo data (Rani Nayak, GRV-1042/0987/0951) + 40+ multilingual cases
│   ├── main.py                 # FastAPI application entrypoint with CORS
│   └── requirements.txt        # Python dependency manifest
├── src/                        # React 18 + TypeScript + Tailwind CSS Frontend
│   ├── services/api.ts         # Centralized API service connecting frontend to FastAPI backend
│   ├── context/                # AuthContext, ComplaintContext, NotificationContext, LanguageContext
│   └── pages/                  # Login, Dashboard, Assistant, Complaints, Detail, Hotspots, Impact
├── .env.example                # Template for Gemini API key and configuration
└── vite.config.ts              # Vite config with /api reverse proxy to http://127.0.0.1:8000
```

---

## 🧠 AI Service Layer Capabilities

1. **Provider-Swappable Extraction**:
   - `extract(text)` returns structured JSON: `{language, translated_text_en, category, sub_category, department, urgency, sentiment, location, summary, confidence}`.
   - When `GEMINI_API_KEY` is provided in `.env`, invokes Gemini with structured JSON output and retry logic.
   - When API key is absent or network fails, automatically falls back to an extensive rule-based multilingual NLP engine.
2. **Code-Mixed & Romanized Input Handling**:
   - Accurately classifies native scripts (`ଓଡ଼ିଆ`, `हिन्दी`, `বাংলা`, `తెలుగు`, `मराठी`, `தமிழ்`) as well as Romanized/transliterated input (Hinglish, Odishlish, Banglish like *"Badambadi re rasta kharap heichi"* or *"Ward 4 me transformer blast ho gaya"*).
3. **Conversational Slot-Filling**:
   - Dynamically tracks slots: `issue`, `category`, `department`, `district`, `area`, `urgency`.
   - Inquires for missing location details in the citizen's preferred language.
   - Presents an interactive confirmation card before filing the formal ticket in the database.
4. **Embedding / TF-IDF Duplicate Detection**:
   - Compares incoming complaints against active tickets within the same district and category to flag potential duplicates.
5. **Knowledge Base RAG**:
   - Indexes public service rules and FAQs from `/backend/kb/` to provide instant policy answers alongside grievance filing.

---

## 📊 Evaluation Benchmarks (`/backend/eval`)

A curated benchmark of 65+ labeled citizen grievances across 5 languages and code-mixed formats is included.

Run evaluation:
```bash
python backend/eval/run_eval.py
```

### Empirical Results
- **Category Classification Accuracy**: **93.85%**
- **Code-Mixed / Transliteration Accuracy**: **90.48%**
- **Language Detection Accuracy**: **84.62%**
- **Average Inference Latency**: **< 1 ms**
- **Confusion Matrix**: Generated and rendered live on the Public Impact page (`/impact`).

---

## 🚀 Setup & Execution Guide

### 1. Environment Setup
Copy the example environment configuration:
```bash
cp .env.example .env
```
*(Optional: Add your `GEMINI_API_KEY` in `.env` to enable Gemini AI processing. If omitted, the high-precision multilingual rule-based fallback handles all classification seamlessly).*

### 2. Backend Setup & Seeding

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Seed database with exact demo data (Rani Nayak, GRV-1042/0987/0951) + 40+ multilingual cases
python backend/seed.py

# Start FastAPI server on port 8000
python backend/main.py
# Or with uvicorn:
# uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup

```bash
# Install node packages
npm install

# Start Vite development server (port 3000, proxies /api -> http://127.0.0.1:8000)
npm run dev
```

Open your browser at `http://localhost:3000`.

---

## 🔑 Demo Credentials

- **Citizen Login**:
  - Mobile: `9876543210` (or any valid 10-digit number starting with 6-9)
  - Mock OTP: `123456`
- **Admin Login**:
  - Employee ID: `OD-ADM-2024-88`
  - Password: `Admin@2026`
- **Guest Mode**:
  - Click "Continue as Guest" to explore grievance filing without persistent account history.
