# 💰 FinanceAI — AI-Powered Personal Finance Assistant

Full-stack personal finance app with AI chat powered by **bytedance/seed-oss-36b-instruct** via NVIDIA API.

## 🚀 Quick Start

### Step 1 — Set your NVIDIA API Key

Edit the `.env` file in the project root:
```
NVIDIA_API_KEY=your_actual_nvidia_api_key_here
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
| Model | `bytedance/seed-oss-36b-instruct` |
| Provider | NVIDIA API (`https://integrate.api.nvidia.com/v1`) |
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
