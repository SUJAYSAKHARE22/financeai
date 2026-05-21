import React, { useState, useEffect, useRef } from 'react'
import { aicaAPI } from '../utils/aica_api'
import { Bot, Send, User, Sparkles, RefreshCw, Shield, AlertCircle, Info } from 'lucide-react'

const SUGGESTED = [
  "How much tax can I save?",
  "Compare old vs new regime",
  "Which expenses are deductible?",
  "Show my business expenses",
]

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} mb-4`}>
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${isUser ? 'bg-emerald-500/20' : 'bg-violet-500/20'}`}>
        {isUser ? <User size={15} className="text-emerald-400" /> : <Bot size={15} className="text-violet-400" />}
      </div>
      <div className={`max-w-[78%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${isUser ? 'bg-emerald-500/15 border border-emerald-500/20 text-slate-200 rounded-tr-sm' : 'bg-obsidian-750 border border-obsidian-500 text-slate-300 rounded-tl-sm shadow-md'}`}>
        {msg.content}
      </div>
    </div>
  )
}

export default function AICAChat({ taxContext = {}, financialContext = {} }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! I am AI-CA, your AI-powered Chartered Accountant assistant. 🏛️\n\nI have evaluated your financial statements and tax context. I can help you compute tax liability under both regimes, identify deductible business and investment expenses, and plan your tax-saving strategy. What can I calculate or clarify for you today?"
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')

    const userMsg = { role: 'user', content: msg }
    const historyForApi = messages.map(m => ({ role: m.role, content: m.content }))

    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await aicaAPI.chat(msg, historyForApi, true)
      const reply = res.data?.reply || "I couldn't process that response. Please ensure GROQ_API_KEY is configured."
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])
    } catch (e) {
      console.error(e)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I had trouble reaching the AI service. If you haven't set up the GROQ_API_KEY in your .env file, please configure it for full CA consulting responses."
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setMessages([
      {
        role: 'assistant',
        content: "Let's start fresh! I'm ready to answer any tax or accounting questions."
      }
    ])
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Chat Area */}
      <div className="lg:col-span-3 flex flex-col border border-obsidian-600 bg-obsidian-800/40 rounded-2xl p-4 min-h-[600px] justify-between shadow-xl backdrop-blur-md">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-obsidian-600">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-emerald-500 flex items-center justify-center shadow">
              <Shield size={16} className="text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-200">AI-CA Chat Assistant</h3>
              <p className="text-[10px] text-slate-500">Tax-aware Expert Guidance</p>
            </div>
          </div>
          <button onClick={handleClear} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 py-1 px-2.5 rounded-lg hover:bg-obsidian-750 transition-all">
            <RefreshCw size={11} /> Clear
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto mb-4 space-y-2 pr-2 max-h-[450px]">
          {messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg} />
          ))}
          {loading && (
            <div className="flex gap-3 mb-4">
              <div className="w-8 h-8 rounded-xl bg-violet-500/20 flex items-center justify-center flex-shrink-0 animate-pulse">
                <Bot size={15} className="text-violet-400" />
              </div>
              <div className="bg-obsidian-750 border border-obsidian-500 px-4 py-3 rounded-2xl rounded-tl-sm text-sm text-slate-400 flex items-center gap-2">
                <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Suggested Queries */}
        {messages.length <= 2 && (
          <div className="pb-3 border-t border-obsidian-700/50 pt-3">
            <p className="text-[11px] text-slate-500 mb-2 font-medium">Quick Consultations:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED.map(s => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="text-xs px-3 py-1.5 bg-obsidian-750 border border-obsidian-600 rounded-xl text-slate-400 hover:text-slate-200 hover:border-violet-500/40 hover:bg-violet-500/5 transition-all text-left"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="border-t border-obsidian-700 pt-3">
          <div className="flex gap-2 items-end">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              placeholder="Ask about deduction rules, HRA calculation, old vs new slabs... (Enter to send)"
              rows={1}
              className="input-field flex-1 resize-none py-3 px-4 text-sm leading-relaxed"
              style={{ minHeight: '44px', maxHeight: '100px' }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="w-11 h-11 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-all flex-shrink-0 shadow-lg shadow-emerald-950/20"
            >
              <Send size={15} className="text-obsidian-900" />
            </button>
          </div>
          <div className="flex items-center justify-center gap-1.5 text-[10px] text-slate-600 mt-2.5">
            <Info size={11} />
            <span>Consultations are tax-aware, using client context. Always consult a real CA before filing.</span>
          </div>
        </div>

      </div>

      {/* Tax Context Panel */}
      <div className="border border-obsidian-600 bg-obsidian-800/20 rounded-2xl p-4 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-obsidian-700">
          <AlertCircle size={14} className="text-violet-400" />
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Active Tax Context</h4>
        </div>

        <div className="space-y-3">
          <div className="p-2.5 rounded-xl bg-obsidian-750 border border-obsidian-600 space-y-1">
            <div className="text-[10px] text-slate-500">Gross tracked income</div>
            <div className="font-mono text-sm font-bold text-slate-200">
              ₹{(taxContext?.gross_income || financialContext?.total_income || 0).toLocaleString('en-IN')}
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-obsidian-750 border border-obsidian-600 space-y-1">
            <div className="text-[10px] text-slate-500">Regime Slab</div>
            <div className="text-xs font-bold text-emerald-400 capitalize">
              {taxContext?.tax_regime || 'New'} Regime
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-obsidian-750 border border-obsidian-600 space-y-1">
            <div className="text-[10px] text-slate-500">Estimated Liability</div>
            <div className="font-mono text-sm font-bold text-rose-400">
              ₹{(taxContext?.total_tax_liability || 0).toLocaleString('en-IN')}
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-obsidian-750 border border-obsidian-600 space-y-1">
            <div className="text-[10px] text-slate-500">Deductions Applied</div>
            <div className="font-mono text-xs text-slate-300">
              - Standard: ₹{(taxContext?.deduction_breakdown?.standard_deduction || 0).toLocaleString('en-IN')}<br/>
              - Sec 80C: ₹{(taxContext?.deduction_breakdown?.section_80c || 0).toLocaleString('en-IN')}<br/>
              - Sec 80D: ₹{(taxContext?.deduction_breakdown?.section_80d || 0).toLocaleString('en-IN')}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
