# 💰 FinanceAI — AI-Powered Personal Finance Assistant

Full-stack personal finance app with AI chat powered by **llama-3.1-8b-instant** via GROQ API.

## 🚀 Quick Start

### Step 1 — Set your groq API Key

Edit the `.env` file in the project root:
```
GROQ_API_KRY=your_actual_groq_api_key_here
```

### Step 2 — Start the Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```
→ Runs at **http://localhost:8000** · Swagger docs at **http://localhost:8000/docs**

### Step 3 — Start the Frontend

```bash
cd frontend
npm install
npm run dev
```
→ Runs at **http://localhost:3000**

---

## 🤖 AI Model

| Setting | Value |
|---|---|
| Model | `llama-3.1-8b-instruct` |
| Temperature | 1.1 |
| Streaming | ✅ Real-time token streaming |
| Thinking | Extended reasoning (`thinking_budget: -1`) |

The AI receives your actual financial context (income, expenses, savings, category breakdown) on every request.

---

## 📁 Structure

```
financeai/
├── .env                        ← Put NVIDIA_API_KEY here
├── .env.example
├── README.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── models/schemas.py
│   ├── routers/
│   │   ├── ai_advisor.py       ← NVIDIA API integration
│   │   ├── transactions.py
│   │   ├── budgets.py
│   │   ├── goals.py
│   │   └── dashboard.py
│   └── services/database.py
└── frontend/
    └── src/
        ├── pages/
        │   ├── AIAdvisor.jsx   ← Streaming chat UI
        │   ├── Dashboard.jsx
        │   ├── Transactions.jsx
        │   ├── Budgets.jsx
        │   └── Goals.jsx
        └── utils/api.js        ← SSE streaming client
```

---

## 📊 Features

- ✅ Dashboard with charts, budget health, goal progress, AI insights
- ✅ Full transaction CRUD with categories
- ✅ Monthly budgets with live progress bars and alerts
- ✅ Financial goals with deadline tracking
- ✅ AI chat with **real-time streaming** (SSE)
- ✅ Context-aware AI (reads your actual financial data)
- ✅ Demo mode (smart rule-based responses if no API key)
- ✅ All amounts in ₹ INR
- ✅ Pre-seeded with realistic demo data
