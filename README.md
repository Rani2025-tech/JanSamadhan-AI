# 🏛️ JanSamadhan — Multilingual Citizen Grievance Redressal Portal

An intelligent, AI-powered multilingual civic grievance redressal and public tracking portal. Empowering citizens across India to report infrastructure failures and public service issues in **English, Hindi (हिन्दी), Odia (ଓଡ଼ିଆ), Marathi (मराठी), Telugu (తెలుగు), and other Indian languages** without bureaucratic friction.

---

## 🎯 Problem Statement & Vision
Citizens often face major hurdles when reporting civic emergencies—bureaucratic forms, complex logins, language barriers, and lack of visibility into resolution timelines. 

**JanSamadhan** provides:
* **Frictionless Citizen Intake**: Report issues conversationally in native languages without creating an account or remembering passwords.
* **Instant Department Routing**: Automatic categorization into 10 municipal departments using low-latency semantic embeddings.
* **Urgency & Hazard Prioritization**: Automatic detection of critical hazards (sparking power lines, pipeline bursts, open manholes) to enforce emergency SLAs.
* **Privacy by Design**: Public ticket tracking displays SLA progression while citizen contact and personal details remain protected behind a secure 6-digit cryptographic PIN.
* **Administrative Triage**: A unified workbench for municipal officials and administrators with automated duplicate clustering and cross-department re-routing.

---

## 💡 Core Capabilities

| Capability | Description |
| :--- | :--- |
| 🗣️ **Multilingual Conversational AI** | Native understanding for English, Hindi, Odia, Marathi, Telugu, Tamil, and Bengali with Indic numeral support (`०-९`, `୦-୯`). |
| ⚡ **Zero-LLM Local Semantic Router** | FastEmbed (`bge-small-en-v1.5`) local classifier routing complaints to the correct department in <50ms. |
| 🛡️ **Provider-Resilient LLM Engine** | High-speed Groq (`llama-3.3-70b-versatile`) extraction with automatic fallback to Google Gemini (`gemini-2.5-flash`). |
| 🚨 **Urgency & Danger Detection** | Scans for Indic hazard keywords to assign Critical/High priority and strict resolution SLAs. |
| 🗂️ **Civic Duplicate Clustering** | Groups duplicate complaints in the same locality into unified clusters to prevent duplicate municipal dispatch. |
| 🔒 **Cryptographic 6-Digit PIN** | Bcrypt-hashed PIN given to the citizen upon filing, required to unlock private contact and grievance details. |
| 🏛️ **Role-Based Staff Workbench** | JWT-authenticated portal with department-level scoping, misroute flagging, and administrative re-routing. |
| 📥 **Official Grievance Receipt** | Generates downloadable text receipts for citizen records and offline follow-up. |

---

## 🛠️ Technology Stack

* **Frontend**: Streamlit, Custom Responsive Purple/Plum Design System ([style.css](frontend/assets/style.css)), Lucide SVG Icons.
* **Backend API**: FastAPI, Uvicorn, Pydantic, HTTPX.
* **Semantic Embeddings**: FastEmbed ONNX runtime (`BAAI/bge-small-en-v1.5`).
* **LLM Engine**: Groq Llama 3.3 70B Versatile + Google Gemini 2.5 Flash Fallback.
* **Database & Storage**: SQLite with idempotent schema migrations (PostgreSQL-ready).
* **Security & Auth**: JWT Bearer Tokens, Bcrypt PIN hashing, Sliding-Window Rate Limiting.
* **Testing**: Comprehensive 83-test Python unittest suite.

---

## 📁 Repository Structure

```
JanSamadhan-AI/
├── backend/
│   ├── api/             # FastAPI route handlers (chat, tracking, staff, admin)
│   ├── core/            # State machine, triage router, embedder, LLM wrapper
│   ├── db/              # Database models, schema migrations, SLA escalation
│   └── main.py          # FastAPI application entrypoint & middleware
├── frontend/
│   ├── app.py           # Streamlit navigation shell & top bar
│   ├── assets/          # Shared CSS design system & variables
│   ├── components.py    # XSS-safe UI components (stepper, cards, receipts)
│   ├── icons.py         # Self-contained SVG icon registry
│   └── views/           # Multi-page views (chat, tracking, staff portal)
├── data/
│   └── departments.json # 10 municipal & civic department taxonomy
├── locales/             # Multilingual string dictionaries (en, hi, or, mr, ta, bn)
├── scripts/             # Demo data seeders and helper scripts
├── tests/               # 83 automated unit and integration tests
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template configuration
└── README.md
```

---

## ⚙️ Quickstart & Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Rani2025-tech/JanSamadhan-AI.git
cd JanSamadhan-AI
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and provide your API keys:
```bash
cp .env.example .env
```
Key configuration values:
* `GROQ_API_KEY`: Groq API key for high-speed extraction.
* `GEMINI_API_KEY`: Google Gemini API key for automatic fallback.
* `JWT_SECRET`: Secret key for signing staff authentication tokens.
* `DEMO_MODE`: Set to `1` to enable one-click evaluation sessions for hackathon judges.

### 5. Start the Services

**Terminal 1 — Backend API Server:**
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend Citizen Portal:**
```bash
streamlit run frontend/app.py
```

Open your browser at `http://localhost:8501` to access the portal.

---

## 🧪 Running the Test Suite
The project includes an automated test suite verifying routing accuracy, Indic digits, PIN encryption, and role permissions:
```bash
python -m unittest discover tests
```

---

## 🇮🇳 Digital Public Infrastructure Initiative
Built with ❤️ for responsive, transparent, and digitally empowered citizen governance.
