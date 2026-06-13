import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { 
  TrendingUp, Shield, Sparkles, Database, Landmark, 
  ArrowRight, UserPlus, LogIn, ChevronRight, MessageSquare, 
  Wallet, PiggyBank, Plus, RotateCcw
} from 'lucide-react'
import { useAuth } from '../components/AuthContext'

export default function Home() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  // Interactive Demo State
  const [demoTransactions, setDemoTransactions] = useState([
    { id: 1, title: 'Freelance Design', amount: 35000, type: 'income', category: 'Freelance' },
    { id: 2, title: 'Rent Payment', amount: 15000, type: 'expense', category: 'Bills & Utilities' },
    { id: 3, title: 'Grocery Store', amount: 4800, type: 'expense', category: 'Food & Dining' }
  ])
  const [newTitle, setNewTitle] = useState('')
  const [newAmount, setNewAmount] = useState('')
  const [newType, setNewType] = useState('expense')
  const [newCategory, setNewCategory] = useState('Shopping')

  // Chatbot State
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AI Finance Advisor. Add some transactions above, and ask me how your budget is looking!' }
  ])
  const [typing, setTyping] = useState(false)

  // Calculations
  const totalIncome = demoTransactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0)
  
  const totalExpense = demoTransactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0)
  
  const netSavings = totalIncome - totalExpense
  const savingsRate = totalIncome > 0 ? (netSavings / totalIncome) * 100 : 0

  // Quick Mock Actions
  const handleAddQuickTransaction = (title, amount, type, category) => {
    const newTx = {
      id: Date.now(),
      title,
      amount,
      type,
      category
    }
    setDemoTransactions(prev => [newTx, ...prev])
  }

  const handleAddCustomTransaction = (e) => {
    e.preventDefault()
    if (!newTitle || !newAmount) return
    const newTx = {
      id: Date.now(),
      title: newTitle,
      amount: parseFloat(newAmount),
      type: newType,
      category: newCategory
    }
    setDemoTransactions(prev => [newTx, ...prev])
    setNewTitle('')
    setNewAmount('')
  }

  const resetDemo = () => {
    setDemoTransactions([
      { id: 1, title: 'Freelance Design', amount: 35000, type: 'income', category: 'Freelance' },
      { id: 2, title: 'Rent Payment', amount: 15000, type: 'expense', category: 'Bills & Utilities' },
      { id: 3, title: 'Grocery Store', amount: 4800, type: 'expense', category: 'Food & Dining' }
    ])
    setChatMessages([
      { role: 'assistant', content: 'Demo dashboard reset. Ask me anything about your current budget!' }
    ])
  }

  const handleAskAI = (question) => {
    if (typing) return
    
    // Add user message
    const userMsg = { role: 'user', content: question }
    setChatMessages(prev => [...prev, userMsg])
    setTyping(true)

    // Simulate AI response based on data
    setTimeout(() => {
      let responseContent = ''
      if (question.includes('savings')) {
        responseContent = `Your current savings are ₹${netSavings.toLocaleString('en-IN')} (${savingsRate.toFixed(1)}% savings rate). ${
          savingsRate >= 30 
            ? "Excellent job! You are exceeding the standard 20% savings rule. Consider allocating ₹" + Math.round(netSavings * 0.4) + " to mutual fund SIPs."
            : "You are currently saving " + savingsRate.toFixed(1) + "%. Aim to trim non-essential categories like shopping to hit a 20% target."
        }`
      } else if (question.includes('tax')) {
        const taxable = Math.max(0, (totalIncome * 12) - 75000) // simple standard deduction
        responseContent = `Based on your simulated income, your projected gross annual income is ₹${(totalIncome * 12).toLocaleString('en-IN')}. Under the New Regime, standard deductions apply. We estimate your taxable salary is around ₹${taxable.toLocaleString('en-IN')}. Connect your account to generate the full form 16 and ITR portals!`
      } else {
        responseContent = `Your total budget overview:
• Income: ₹${totalIncome.toLocaleString('en-IN')}
• Expense: ₹${totalExpense.toLocaleString('en-IN')}
• Savings: ₹${netSavings.toLocaleString('en-IN')} (${savingsRate.toFixed(1)}%)

Highest expenses observed in Bills and Grocery categories. Try budgeting ₹10,000 for shopping next month.`
      }

      setChatMessages(prev => [...prev, { role: 'assistant', content: responseContent }])
      setTyping(false)
    }, 1200)
  }

  return (
    <div className="min-h-screen bg-obsidian-900 text-slate-200 font-sans relative overflow-x-hidden">
      {/* Glow backgrounds */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] rounded-full bg-violet-600/5 blur-[120px] pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-[600px] h-[600px] rounded-full bg-emerald-500/5 blur-[150px] pointer-events-none" />

      {/* Navigation header */}
      <header className="border-b border-obsidian-600/50 glass sticky top-0 z-50 transition-all duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-violet-500 flex items-center justify-center shadow-lg shadow-emerald-500/10">
              <TrendingUp size={18} className="text-white" />
            </div>
            <div>
              <div className="text-lg font-bold text-slate-100 tracking-tight">FinanceAI</div>
              <div className="text-[10px] text-emerald-400 font-medium tracking-wide">Smart Money Assistant</div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <button 
                onClick={() => navigate('/dashboard')}
                className="btn-primary flex items-center gap-2"
              >
                Go to Dashboard <ArrowRight size={16} />
              </button>
            ) : (
              <>
                <Link to="/login" className="text-slate-400 hover:text-slate-200 text-sm font-semibold transition-colors flex items-center gap-1.5 px-3 py-2 rounded-xl hover:bg-obsidian-800">
                  <LogIn size={16} /> Log In
                </Link>
                <Link to="/signup" className="btn-primary flex items-center gap-1.5 py-2 px-4 shadow-lg shadow-emerald-500/10">
                  <UserPlus size={16} /> Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20 relative z-10 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-semibold tracking-wide mb-8 animate-pulse">
          <Shield size={13} /> Private SQLite Storage • Fully Localized
        </div>
        
        <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-100 tracking-tight max-w-4xl mx-auto leading-none">
          Manage your money with{' '}
          <span className="bg-gradient-to-r from-emerald-400 via-teal-400 to-violet-400 bg-clip-text text-transparent">
            Absolute Privacy
          </span>
        </h1>
        
        <p className="mt-6 text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          FinanceAI is an intelligent money manager, tax calculator, and ledger bookkeeper that runs on a secure local SQLite database. Track goals, analyze budgets, and file ITR forms safely.
        </p>

        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <Link to="/signup" className="btn-primary py-3.5 px-8 text-base shadow-xl shadow-emerald-500/15 flex items-center gap-2 hover:scale-[1.02] transition-transform">
            Start Free Account <ChevronRight size={18} />
          </Link>
          <a href="#interactive-demo" className="btn-secondary py-3.5 px-8 text-base flex items-center gap-2 hover:scale-[1.02] transition-transform">
            Try Live Demo
          </a>
        </div>

        {/* Feature stats summary cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-20 text-left">
          <div className="card p-6 border-obsidian-600/60 bg-obsidian-800/40 backdrop-blur-sm">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 mb-4 border border-emerald-500/15">
              <Database size={20} />
            </div>
            <h3 className="text-base font-bold text-slate-200">Local SQLite DB</h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Your entries, taxpayer profiles, and statements are stored locally in isolated SQLite tables. Zero data sharing.
            </p>
          </div>

          <div className="card p-6 border-obsidian-600/60 bg-obsidian-800/40 backdrop-blur-sm">
            <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center text-violet-400 mb-4 border border-violet-500/15">
              <Sparkles size={20} />
            </div>
            <h3 className="text-base font-bold text-slate-200">AI Advisor Advice</h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              An intelligent, context-aware advisor that analyzes your transactions to guide your mutual fund SIP allocations.
            </p>
          </div>

          <div className="card p-6 border-obsidian-600/60 bg-obsidian-800/40 backdrop-blur-sm">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 mb-4 border border-amber-500/15">
              <Landmark size={20} />
            </div>
            <h3 className="text-base font-bold text-slate-200">AI Chartered Accountant</h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Automates tax filing, categorizes business items, tracks section 80C deductions, and downloads filled ITR-1 PDFs.
            </p>
          </div>

          <div className="card p-6 border-obsidian-600/60 bg-obsidian-800/40 backdrop-blur-sm">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 flex items-center justify-center text-teal-400 mb-4 border border-teal-500/15">
              <Shield size={20} />
            </div>
            <h3 className="text-base font-bold text-slate-200">Zero Tenancy Bleed</h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Every user logs in to their own completely personalized database workspace. Other users can never read your logs.
            </p>
          </div>
        </div>
      </section>

      {/* Interactive Demo Section */}
      <section id="interactive-demo" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 relative border-t border-obsidian-600/40">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-extrabold text-slate-100">
            Interactive Playground Demo
          </h2>
          <p className="text-slate-400 text-sm mt-3 max-w-xl mx-auto">
            Test drive our dashboard features below. Add transactions to the mock panel, and see the numbers and AI adviser adapt instantly!
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left panel: Add transaction form and recent transactions list */}
          <div className="lg:col-span-5 space-y-6">
            <div className="card p-5 border-obsidian-600 bg-obsidian-800/60">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-200">Mock Data Control Panel</h3>
                <button 
                  onClick={resetDemo} 
                  className="p-1 text-slate-500 hover:text-slate-300 rounded-lg hover:bg-obsidian-750 transition-colors flex items-center gap-1 text-xs font-semibold"
                  title="Reset demo data"
                >
                  <RotateCcw size={14} /> Reset
                </button>
              </div>

              {/* Quick transaction buttons */}
              <div className="mb-6 space-y-2">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Quick Add Presets</div>
                <div className="grid grid-cols-2 gap-2">
                  <button 
                    onClick={() => handleAddQuickTransaction('Salary Credit', 80000, 'income', 'Salary')}
                    className="flex items-center gap-1.5 justify-center py-2 px-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/15 transition-all text-xs font-semibold"
                  >
                    <Plus size={14} /> +₹80,000 Salary
                  </button>
                  <button 
                    onClick={() => handleAddQuickTransaction('SIP Mutual Fund', 12000, 'expense', 'Investment')}
                    className="flex items-center gap-1.5 justify-center py-2 px-3 rounded-xl bg-violet-500/10 text-violet-400 border border-violet-500/20 hover:bg-violet-500/15 transition-all text-xs font-semibold"
                  >
                    <Plus size={14} /> -₹12,000 SIP
                  </button>
                  <button 
                    onClick={() => handleAddQuickTransaction('Amazon Shopping', 3200, 'expense', 'Shopping')}
                    className="flex items-center gap-1.5 justify-center py-2 px-3 rounded-xl bg-slate-500/10 text-slate-400 border border-slate-500/20 hover:bg-slate-500/15 transition-all text-xs font-semibold"
                  >
                    <Plus size={14} /> -₹3,200 Shop
                  </button>
                  <button 
                    onClick={() => handleAddQuickTransaction('Zomato Delivery', 1150, 'expense', 'Food & Dining')}
                    className="flex items-center gap-1.5 justify-center py-2 px-3 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/15 transition-all text-xs font-semibold"
                  >
                    <Plus size={14} /> -₹1,150 Dining
                  </button>
                </div>
              </div>

              {/* Custom Add form */}
              <form onSubmit={handleAddCustomTransaction} className="space-y-4 pt-4 border-t border-obsidian-600">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Add Custom Record</div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <input 
                      type="text" 
                      placeholder="Title (e.g. Uber Ride)" 
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      className="input-field py-2 text-xs"
                      required
                    />
                  </div>
                  <div>
                    <input 
                      type="number" 
                      placeholder="Amount (₹)" 
                      value={newAmount}
                      onChange={(e) => setNewAmount(e.target.value)}
                      className="input-field py-2 text-xs"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <select 
                      value={newType} 
                      onChange={(e) => setNewType(e.target.value)}
                      className="input-field py-2 text-xs"
                    >
                      <option value="expense">Expense</option>
                      <option value="income">Income</option>
                    </select>
                  </div>
                  <div>
                    <select 
                      value={newCategory} 
                      onChange={(e) => setNewCategory(e.target.value)}
                      className="input-field py-2 text-xs"
                    >
                      <option value="Food & Dining">Food & Dining</option>
                      <option value="Bills & Utilities">Bills & Utilities</option>
                      <option value="Shopping">Shopping</option>
                      <option value="Investment">Investment</option>
                      <option value="Salary">Salary</option>
                    </select>
                  </div>
                </div>

                <button 
                  type="submit"
                  className="w-full btn-primary py-2 text-xs font-bold"
                >
                  Insert Transaction Record
                </button>
              </form>
            </div>

            {/* List of demo records */}
            <div className="card p-5 border-obsidian-600 bg-obsidian-800/60 max-h-[300px] overflow-y-auto">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Simulated Ledger</h3>
              <div className="space-y-3">
                {demoTransactions.map(t => (
                  <div key={t.id} className="flex items-center justify-between py-2 border-b border-obsidian-600 last:border-0 text-xs">
                    <div className="flex items-center gap-2.5">
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold ${
                        t.type === 'income' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        {t.category[0]}
                      </div>
                      <div>
                        <div className="font-semibold text-slate-200">{t.title}</div>
                        <div className="text-[10px] text-slate-500">{t.category}</div>
                      </div>
                    </div>
                    <span className={`font-mono font-bold ${t.type === 'income' ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {t.type === 'income' ? '+' : '-'}₹{t.amount.toLocaleString('en-IN')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right panel: Mini dashboard layout & chat interaction */}
          <div className="lg:col-span-7 space-y-6">
            {/* Stat row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="card p-4 border-emerald-500/25 bg-emerald-500/5">
                <div className="text-[10px] font-semibold text-emerald-400/80 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Wallet size={12} /> Income
                </div>
                <div className="font-mono text-sm font-bold text-emerald-400">
                  ₹{totalIncome.toLocaleString('en-IN')}
                </div>
              </div>

              <div className="card p-4 border-rose-500/25 bg-rose-500/5">
                <div className="text-[10px] font-semibold text-rose-400/80 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <TrendingUp size={12} className="rotate-180" /> Expenses
                </div>
                <div className="font-mono text-sm font-bold text-rose-400">
                  ₹{totalExpense.toLocaleString('en-IN')}
                </div>
              </div>

              <div className="card p-4 border-violet-500/25 bg-violet-500/5">
                <div className="text-[10px] font-semibold text-violet-400/80 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <PiggyBank size={12} /> Net Savings
                </div>
                <div className="font-mono text-sm font-bold text-violet-400">
                  {netSavings < 0 ? '-' : ''}₹{Math.abs(netSavings).toLocaleString('en-IN')}
                </div>
              </div>

              <div className="card p-4 border-amber-500/25 bg-amber-500/5">
                <div className="text-[10px] font-semibold text-amber-400/80 uppercase tracking-wider mb-1 flex items-center gap-1">
                  Rate
                </div>
                <div className="font-mono text-sm font-bold text-amber-400">
                  {savingsRate.toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Savings gauge visualization */}
            <div className="card p-5 border-obsidian-600 bg-obsidian-800/60">
              <div className="flex justify-between items-center text-xs mb-2.5">
                <span className="font-bold text-slate-300">Savings Target (Goal: 20%)</span>
                <span className={`font-mono font-bold ${savingsRate >= 20 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {savingsRate.toFixed(1)}% / 20%
                </span>
              </div>
              <div className="h-3 rounded-full bg-obsidian-900 overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-700 bg-gradient-to-r ${
                    savingsRate >= 20 ? 'from-emerald-500 to-teal-400 shadow-md shadow-emerald-500/10' : 'from-amber-500 to-orange-400'
                  }`}
                  style={{ width: `${Math.min(Math.max(savingsRate, 0), 100)}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-500 mt-2">
                *The 50/30/20 rule suggests saving at least 20% of net monthly income for financial independence.
              </p>
            </div>

            {/* AI Advisor chatbot window */}
            <div className="card border-violet-500/20 bg-obsidian-800/60 flex flex-col h-[320px]">
              <div className="flex items-center gap-2 p-4 border-b border-obsidian-600 text-xs font-bold text-slate-200 bg-obsidian-800">
                <div className="w-2.5 h-2.5 bg-violet-400 rounded-full animate-pulse" />
                <MessageSquare size={14} className="text-violet-400" />
                Mock Advisor Chatbot
              </div>
              
              {/* Chat log */}
              <div className="flex-1 p-4 overflow-y-auto space-y-3 scrollbar-thin">
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`p-3 rounded-2xl max-w-[85%] text-xs leading-relaxed ${
                      msg.role === 'user' 
                        ? 'bg-violet-600 text-white rounded-br-none' 
                        : 'bg-obsidian-700 border border-obsidian-600 text-slate-300 rounded-bl-none'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {typing && (
                  <div className="flex justify-start">
                    <div className="p-3 rounded-2xl bg-obsidian-750 text-slate-500 text-xs rounded-bl-none flex items-center gap-1">
                      <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" />
                      <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                      <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:0.4s]" />
                    </div>
                  </div>
                )}
              </div>

              {/* Chat action items */}
              <div className="p-3 border-t border-obsidian-600 bg-obsidian-850 flex gap-2">
                <button 
                  onClick={() => handleAskAI('Analyze my savings rate')}
                  className="flex-1 py-2 rounded-xl bg-violet-500/10 text-violet-400 border border-violet-500/20 hover:bg-violet-500/15 transition-all text-xs font-semibold text-center"
                >
                  Analyze Savings
                </button>
                <button 
                  onClick={() => handleAskAI('What is my tax summary?')}
                  className="flex-1 py-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/15 transition-all text-xs font-semibold text-center"
                >
                  Tax Estimator
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-obsidian-600/30 bg-obsidian-950 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <div className="flex justify-center items-center gap-2 text-sm text-slate-500 font-bold">
            <TrendingUp size={16} className="text-emerald-400" /> FinanceAI Platform
          </div>
          <p className="text-xs text-slate-600 max-w-md mx-auto">
            © 2026 FinanceAI. Secure SQLite local storage framework. No financial advisory or warranty implied.
          </p>
        </div>
      </footer>
    </div>
  )
}
