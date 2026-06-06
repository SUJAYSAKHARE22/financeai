# 💰 FinanceAI — AI-Powered Personal Finance & Tax E-Filing Assistant

FinanceAI is a modern, full-stack personal finance application. It combines traditional wealth management (tracking transactions, budgets, savings goals) with an advanced **AI Chartered Accountant (AI-CA)** engine that automates Indian Income Tax computations, double-entry ledger/journal bookkeeping, financial statements generation, and official tax documents (ITR-1 portal JSON, Form 16, Form 26AS PDFs).

---

## 🚀 Key Modules & Features

### 1. 📊 Personal Finance Management (PFM)
- **Interactive Dashboard**: Modern glassmorphism charts tracking income, expenses, net savings, budget health, goal progress, and automated AI financial insights.
- **Transactions Management**: Complete CRUD interface for logging income and expenses under standard categories.
- **Monthly Budgets**: Live progress tracking and alert systems for monthly caps.
- **Savings Goals**: Goal-oriented savings tracking with automated target deadlines.
- **AI Financial Advisor**: Real-time streaming chat utilizing client context.

### 2. 🛡️ AI Chartered Accountant (AI-CA)
- **Transaction Classifier**: Uses a rule engine coupled with LLM intelligence to auto-classify transactions for tax reporting and map deduplication flags.
- **Indian Income Tax Calculations**: Compares estimated tax liabilities under the **Old Regime** and **New Regime** (including Chapter VI-A deductions, rebate u/s 87A, education cess, standard deductions).
- **Financial Statements**: Dynamically generates Profit & Loss (P&L) statements, Cash Flow summaries, and detailed Expense Breakdowns.
- **Double-Entry Accounting Ledger**: Converts cash-flow transactions into professional double-entry account ledger entries, journal entries, and summaries.
- **Ready-to-File Document Exporter**:
  - **ITR-1 Sahaj JSON**: Generates portal-compatible JSON payloads ready for direct upload to the official `incometax.gov.in` portal.
  - **Official Return Acknowledgement PDF**: Computes and populates a government-style Form ITR-1 Sahaj PDF.
  - **Form 16 Tax Certificate PDF**: Generates Section 203 tax computation certificates.
  - **Form 26AS TDS Credit Sheet PDF**: Reconciles tax deducted at source from verified income descriptors.
  - **Excel/PDF Reports**: Financial overview and statement data downloads.
- **AI-CA Chat Assistant**: Personal tax consulting chat referencing actual client context, standard deduction limits, and Indian tax laws (supports an offline rules-based demo mode).

---

## 📁 Repository Structure

```
financeai/
├── .env                        ← Local configuration (GROQ_API_KEY)
├── .env.example
├── README.md
├── start.sh                    ← Script to run both frontend and backend concurrently
├── backend/
│   ├── main.py                 ← FastAPI router initialization and server configuration
│   ├── requirements.txt        ← Backend dependencies (FastAPI, Groq, ReportLab, Openpyxl)
│   ├── test_itr_generation.py  ← Integration test suite for document generation services
│   ├── models/
│   │   ├── schemas.py          ← Core Pydantic schemas (Transactions, Budgets, Goals)
│   │   └── aica_schemas.py     ← AI-CA schemas (Taxpayer Profile, Tax calculations, Ledgers)
│   ├── routers/
│   │   ├── ai_advisor.py       ← Standard AI chat router
│   │   ├── aica_router.py      ← AI-CA endpoints (classify, tax-summary, statements, ledger, reports, ITR docs)
│   │   ├── transactions.py
│   │   ├── budgets.py
│   │   ├── goals.py
│   │   └── dashboard.py
│   └── services/
│       ├── database.py         ← Seeded in-memory store for transactions, budgets, goals, and taxpayer profiles
│       ├── aica_chat_service.py← Tax-aware AI-CA chat advisor via Groq (with rules-based fallback)
│       ├── classifier_service.py← Enriches transactions using rule matching and LLM categorization
│       ├── itr_generator.py    ← PDF & JSON document generator using ReportLab (ITR-1 Sahaj, Form 16, Form 26AS)
│       ├── ledger_engine.py    ← Translates transactions into double-entry accounting records
│       ├── report_generator.py ← Financial statement PDF/Excel report exporter
│       ├── rule_engine.py      ← Categorization rules and tax flag maps
│       ├── statement_engine.py ← Generates P&L, Cash Flow, and Tax summaries
│       └── tax_engine.py       ← Slabs implementation for Old/New regimes (FY 2024-25 / AY 2025-26)
└── frontend/
    ├── package.json
    ├── tailwind.config.js
    ├── vite.config.js          ← Proxies API calls to localhost:8000
    └── src/
        ├── App.jsx             ← Main layout with routes: Dashboard, Transactions, Budgets, Goals, AI Advisor, and AI-CA
        ├── main.jsx
        ├── components/
        │   ├── Sidebar.jsx     ← Navigation sidebar listing all major views
        │   └── AICAChat.jsx    ← Conversational AI CA chat screen
        ├── pages/
        │   ├── Dashboard.jsx   ← Interactive financial analytics dashboard
        │   ├── Transactions.jsx← CRUD tables for transactions
        │   ├── Budgets.jsx     ← Budget control cards
        │   ├── Goals.jsx       ← Savings progress page
        │   ├── AIAdvisor.jsx   ← Standard AI streaming chat page
        │   └── AICADashboard.jsx← Full AI-CA Dashboard (Overview stats, Tax calculation table, P&L, Docs download, Profile form)
        └── utils/
            ├── api.js          ← Standard app API handler
            ├── aica_api.js     ← Dedicated client endpoints for AI-CA
            └── format.js       ← Currency & styling formatters
```

---

## 🛠️ Getting Started

### Prerequisites
- **Python** 3.10+
- **Node.js** v18+ & **npm**

### Step 1: Configure Environment Variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_actual_groq_api_key_here
```
> [!NOTE]
> If no `GROQ_API_KEY` is provided, the application runs in a high-fidelity **Demo Mode**, utilizing rule-based intelligence for transaction classification and interactive tax consultation.

### Step 2: Running the Application

You can spin up both the backend server and frontend client concurrently using the provided start script:

```bash
chmod +x start.sh
./start.sh
```

Alternatively, you can run the services individually:

#### Start the Backend:
```bash
cd backend
pip install -r requirements.txt
python main.py
```
- Server API runs at: **http://localhost:8000**
- Swagger documentation: **http://localhost:8000/docs**

#### Start the Frontend:
```bash
cd frontend
npm install
npm run dev
```
- Client runs at: **http://localhost:3000**

---

## 🧪 Testing Document Generation
To run the automated integration test suite for the ReportLab PDF and JSON e-filing file exports, run:
```bash
cd backend
python test_itr_generation.py
```
It validates the creation of:
1. Ready-to-file Form ITR-1 Sahaj JSON.
2. Official ITR-1 Sahaj Form PDF.
3. Form 16 Tax Summary PDF.
4. Form 26AS TDS Statement PDF.
