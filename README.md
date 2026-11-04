# JanSamadhan - Multilingual Citizen Grievance Redressal Portal

JanSamadhan is an AI-powered, multilingual civic grievance redressal and public administration platform designed for the State of Odisha and scalable across India. It connects citizens with government departments (PHED, PWD, DISCOM, Municipal Corporations, Health, PDS) via natural conversational interfaces in 7 Indian languages (Odia, Hindi, Bengali, Telugu, Marathi, Tamil, English), accompanied by real-time GIS hotspot telemetry, automated duplicate triage, and SLA tracking for administrative nodal officers.

---

## 🎯 Problem Statement & Track

- **Track Code**: **Human Impact (HI-02)**
- **Track Name**: `[TODO: Official Track Name]`
- **Problem Statement**: Millions of citizens face barriers when reporting critical civic grievances—broken water mains, sparking high-voltage electrical lines, contaminated drinking supplies, and impassable road craters—due to complex administrative portals, rigid forms, and lack of support for regional languages or Romanized/code-mixed dialects. JanSamadhan solves this by offering an intuitive, voice-enabled, multilingual conversational agent with deterministic offline fallback and automated officer escalation.

---

## 👥 Team Details

- **Lead Developer & Submitter**: Rani Nayak (`rani.nayak.tech25@gmail.com`)
- **Team Members & Roles**: `[TODO: Team Member Names, Institutional Affiliations, and Specific Roles]`

---

## ✨ Features

- **7-Language Native & Transliterated Support**: Full bidirectional support for Odia (`ଓଡ଼ିଆ`), Hindi (`हिन्दी`), Bengali (`বাংলা`), Telugu (`తెలుగు`), Marathi (`मराठी`), Tamil (`தமிழ்`), and English (`en`), including code-mixed dialects (Odishlish, Hinglish, Banglish).
- **Conversational Slot-Filling AI**: 3-turn interactive state machine that detects missing grievance parameters (e.g., location/landmark), clarifies details in the citizen's language, and renders a structured confirmation card before filing.
- **Provider-Swappable AI Architecture**: Powered by Google Gemini 2.5 Flash for deep contextual reasoning, zero-shot entity extraction, and RAG over civic FAQs; automatically falls back to an internal deterministic multilingual rule-based NLP engine when offline.
- **Cross-Lingual Duplicate Detection**: Multilingual embedding and lexical similarity detector that cross-matches grievances filed in different scripts (e.g., an Odia report and a Hindi report for the same transformer burnout in Ward 7) to prevent redundant officer dispatches.
- **Dynamic GIS Hotspot Telemetry**: Leaflet map displaying real-time grievance clusters across all 30 districts of Odisha (and national views) with proportional radius scaling and severity color-coding.
- **Role-Based Clean-Slate Isolation**: Strict token authentication isolating citizen complaints, notifications, and chat histories; new citizen registrations start with a completely clean slate with zero data leakage.
- **Accessibility & Inclusion**: WCAG AAA-compliant font scaling (A- / A / A+), high-contrast theme, Web Speech voice input, and Web Speech text-to-speech with device voice fallback warnings.

---

## 🛠️ Tech Stack Table

| Layer | Component / Tool | Details |
|:---|:---|:---|
| **Frontend Framework** | React 18 + TypeScript | Component-driven SPA with strict typing |
| **Build & Tooling** | Vite 5 | Fast HMR and Rollup production bundling |
| **Styling & Theme** | Tailwind CSS + Lucide Icons | Custom Odisha government design system |
| **GIS & Mapping** | Leaflet + React-Leaflet | OpenStreetMap tiles, proportional circle markers |
| **Backend Framework** | FastAPI (Python 3.13) | Asynchronous REST API, OpenAPI docs |
| **ORM & Database** | SQLAlchemy 2.0 + SQLite | Relational database (supports PostgreSQL / MySQL) |
| **Authentication** | PyJWT (HS256) | Scoped citizen, guest, and admin bearer tokens |
| **Generative LLM** | Google Gemini 2.5 Flash | Zero-shot extraction, conversational slot filling, RAG |
| **Embeddings** | Gemini `text-embedding-004` | 768-dimensional semantic cross-lingual vectors |
| **Rule-Based Fallback** | Custom Regex & Lexicons | Zero-crash fallback engine for offline reliability |

---

## 🧠 Architecture & AI Pipeline

```
+-----------------------------------------------------------------------------------+
|                                 CITIZEN INTERFACE                                 |
|  [Voice / Mic Dictation]    [Multilingual Text Input]    [Manual Grievance Form]  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                              API GATEWAY / FASTAPI                                |
|  [Rate Limiter (429)]    [JWT Security & Scoping]    [Input Sanitization & Masking]|
+-----------------------------------------+-----------------------------------------+
                                          |
                   +----------------------+----------------------+
                   |                                             |
                   v                                             v
+--------------------------------------+   +---------------------------------------+
|        PRIMARY HOSTED API LAYER      |   |       OFFLINE DETERMINISTIC NLP       |
|  - Google Gemini 2.5 Flash LLM       |   |  - Regex Unicode Block Script Detector|
|  - Gemini Multilingual Embeddings    |   |  - Transliteration Lexicon (7 langs)  |
|  - Zero-shot JSON Slot Filling       |   |  - State / District Routing Rules     |
|  - RAG FAQ Vector Similarity         |   |  - Lexical Urgency Scoring Heuristic  |
+--------------------------------------+   +---------------------------------------+
                   |                                             |
                   +----------------------+----------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                              PERSISTENCE & TELEMETRY                              |
|  [SQLAlchemy Models]  [Status History Audit]  [Notifications]  [GIS Hotspot Aggs] |
+-----------------------------------------------------------------------------------+
```

### Pipeline Components Classification
1. **Rule-Based Engine**: Regex Unicode script detection, Romanized keyword lexicons for Odia/Hindi/Bengali/Telugu/Marathi/Tamil, administrative department routing tables, urgency keyword scoring heuristic, PII regex masking.
2. **Pretrained Hosted Models**: Google Gemini 2.5 Flash (`gemini-2.5-flash`) via `google-genai` SDK and Gemini Embedding model (`text-embedding-004`).
3. **Locally Trained Models**: **None**. (No custom scikit-learn or PyTorch models were trained or serialized; all dependencies are kept lean).

---

## 🚀 Setup & Execution Guide

### Prerequisites
- Node.js 18+ (Node 20+ recommended)
- Python 3.10+ (Python 3.13 tested)
- Git

### 1. Environment Configuration
Clone the repository and copy the environment configuration:
```bash
cp .env.example .env
```
Configure your `.env` file with your credentials:
```env
# Gemini API Key (get from https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# Rotated Authentication Secrets (Required in production)
JWT_SECRET=your_rotated_jwt_secret_here
ADMIN_EMPLOYEE_ID=OD-ADM-2024-88
ADMIN_PASSWORD=your_rotated_admin_password_here
ADMIN_EMAIL=alok.mohapatra@odisha.gov.in
```

### 2. Backend Setup & Seeding
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Seed database with initial demo records and district distribution
python backend/seed.py

# Start FastAPI server on port 8000
python backend/main.py
```

### 3. Frontend Setup
```bash
# Install npm dependencies
npm install

# Start Vite dev server on port 3000 (proxies /api -> http://127.0.0.1:8000)
npm run dev
```

### 4. Docker Single-Container Deployment
```bash
# Build multi-stage container
docker build -t jansamadhan-ai .

# Run container exposing port 8000
docker run -p 8000:8000 --env-file .env jansamadhan-ai
```

### 🔑 Demo Credentials
- **Citizen Login**: Enter any valid 10-digit Indian mobile number (e.g. `9876543210`) and enter the demonstration OTP: **`123456`** *(Demo OTP stub)*.
- **Admin Officer Login**:
  - Employee ID: `OD-ADM-2024-88` (or `alok.mohapatra@odisha.gov.in`)
  - Password: Read from `ADMIN_PASSWORD` in your `.env` file.
- **Guest Citizen**: Click "Continue as Guest" on the login screen.

---

## 📸 Screenshots

| View | Screenshot Preview |
|:---|:---|
| **Citizen Login & Accessibility** | ![Login Screen](docs/screenshots/login.png) |
| **Citizen Redressal Dashboard** | ![Dashboard](docs/screenshots/dashboard.png) |
| **Odia Conversational AI Assistant** | ![Odia Chat Assistant](docs/screenshots/odia_chat.png) |
| **Grievance Detail & SLA Stepper** | ![Complaint Detail](docs/screenshots/complaint_detail.png) |
| **Nodal Officer Admin Registry** | ![Admin Management](docs/screenshots/admin.png) |
| **Civic Hotspot Telemetry Map** | ![Hotspot Map](docs/screenshots/hotspot_map.png) |

---

## 🌐 Live Deployment & Demonstration

- **Live Web Portal**: [https://jansamadhan-ai-gf3o.onrender.com/](https://jansamadhan-ai-gf3o.onrender.com/)
- **Demonstration Video Walkthrough**: `[TODO: Link to 3-minute Demonstration Video Walkthrough]`

---

## 📊 Evaluation Benchmarks (`backend/eval`)

The JanSamadhan evaluation benchmark contains **$n=95$ labeled civic grievances** split strictly into a **Training Set ($n=65$)** and a **Held-Out Test Set ($n=30$)** across 6 civic classes and 7 languages.

### Side-by-Side Evaluation Benchmark

| Metric | Fallback Mode (Train $n=65$) | Fallback Mode (Held-Out $n=30$) | Gemini Mode (Overall $n=95$) |
|:---|:---:|:---:|:---:|
| **Language Detection** | 100.0% (65/65) | 93.33% (28/30) | 98.95% (94/95) |
| **Category Classification** | 90.77% (59/65) | 100.0% (30/30) | 96.84% (92/95) |
| **Urgency Detection (Exact)** | 26.15% (17/65) | 56.67% (17/30) | 94.74% (90/95) |
| **Location Extraction** | N/A (unannotated) | 100.0% (10/10) | 100.0% (10/10) |
| **Code-Mixed Dialect Accuracy** | 95.24% (20/21) | 100.0% (5/5) | 96.15% (25/26) |
| **Average Latency** | 20.53 ms | 15.42 ms | 286.32 ms |

### Cross-Language Duplicate Detection Benchmark
- **Cross-Language Positive Pairs**: 9/10 detected (90.0% Recall)
- **Different Category/District Negative Pairs**: 10/10 correctly rejected (100.0% True Negative Rate; 0.0% False Positive Rate)
- **Precision**: 100.0% (9/9)

---

## ⚠️ Limitations

1. **Synthetic Evaluation Ground-Truth**: The evaluation dataset was generated synthetically from demographic templates to mimic real-world dialect patterns; human adjudication benchmark (`heldout_human.json`) contains 30 reserved slots awaiting blind officer scoring.
2. **Offline Rule-Based Urgency Detection**: In fallback mode without Gemini, urgency detection achieves 56.67% on held-out samples because complex situational urgency requires nuanced semantic comprehension.
3. **Device-Dependent Voice Synthesis**: Web Speech API audio output quality for Odia depends on device-installed TTS packages; browsers without native Odia voices display an automated warning and fall back to Hindi/English audio.
4. **Mock Authentication**: OTP delivery is currently simulated via a demonstration stub (`123456`) and requires integration with CDAC or telecom SMS gateways for government deployment.
5. **Local Attachment Previews**: File upload inputs on the complaint form validate and preview attachments locally (up to 5MB, PNG/JPG/PDF) without storing them on the database server.

---

## 🛡️ Responsible AI & Safety

- **PII Redaction**: Phone numbers (`[PHONE_MASKED]`), 12-digit Aadhaar numbers (`[ID_12DIGIT_REDACTED]`), and email addresses (`[EMAIL_REDACTED]`) are masked prior to any external LLM invocation.
- **Human-in-the-Loop Thresholding**: Any classification with confidence below 0.60 is flagged for mandatory nodal officer manual review.
- **Admin Correction Tracking**: Every officer reassignment of category or department is logged in `AdminCorrection` audit rows to monitor model drift and officer alignment.
- **Prompt Injection Defense**: Multi-turn prompts strictly encapsulate citizen input as data to prevent system prompt extraction or instruction manipulation.

---

## 🤖 AI Tools Disclosure

In accordance with competition guidelines, the following AI tools and models were used during the creation and operation of this project:
- **Antigravity**: Used as the primary agentic AI programming assistant for codebase scaffolding, testing, and full-stack implementation.
- **Claude**: Used for architectural planning, test matrix design, prompt engineering, and UI UX review.
- **Google Gemini API (`gemini-2.5-flash`)**: Runtime generative model powering conversational slot-filling, multilingual reasoning, and RAG search.
- **Image Generation AI**: Used for generating UI mockups and the Odisha login background art.

---

## 📜 Credits and Licences

This software is released under the **MIT License**. See [`LICENSE`](LICENSE) for full details.

- **OpenStreetMap**: Map tiles and geographical coordinates (ODbL License).
- **Leaflet & React-Leaflet**: BSD-2 License.
- **Lucide Icons**: ISC License.
- **Google Noto Fonts**: SIL Open Font License 1.1.
- **React**: MIT License.
- **FastAPI**: MIT License.
- **Google GenAI SDK**: Subject to Google Generative AI Terms of Service.
