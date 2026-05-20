import React, { useState, useEffect, useRef } from 'react'
import { aiAPI } from '../utils/api'
import { Bot, Send, User, Sparkles, RefreshCw, Lightbulb } from 'lucide-react'

const SUGGESTED = [
  "How can I improve my savings rate?",
  "Analyze my spending patterns",
  "Where should I invest my savings?",
  "How to build an emergency fund?",
  "Reduce my monthly expenses",
  "Create a budget plan for me",
]

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} mb-4`}>
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${isUser ? 'bg-emerald-500/20' : 'bg-violet-500/20'}`}>
        {isUser ? <User size={15} className="text-emerald-400" /> : <Bot size={15} className="text-violet-400" />}
      </div>
      <div className={`max-w-[78%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${isUser ? 'bg-emerald-500/15 border border-emerald-500/20 text-slate-200 rounded-tr-sm' : 'bg-obsidian-700 border border-obsidian-500 text-slate-300 rounded-tl-sm'}`}>
        {msg.content}
        {msg.streaming && <span className="inline-block w-1.5 h-4 bg-violet-400 ml-0.5 animate-pulse align-middle" />}
      </div>
    </div>
  )
}

export default function AIAdvisor() {
  const [messages, setMessages] = useState([{
    role: 'assistant',
    content: "Hello! I'm FinanceAI, your personal finance advisor powered by ByteDance Seed OSS. 💰\n\nI have access to your financial data and can help with budgeting, savings, investments, and more. What would you like to explore today?"
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [insights, setInsights] = useState([])
  const bottomRef = useRef(null)

  useEffect(() => { aiAPI.getInsights().then(r => setInsights(r.data.insights)).catch(() => {}) }, [])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const sendMessage = async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')

    const userMsg = { role: 'user', content: msg }
    const history = messages.map(m => ({ role: m.role, content: m.content }))
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    // Add placeholder streaming message
    const placeholderId = Date.now()
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true, id: placeholderId }])

    try {
      let accumulated = ''
      await aiAPI.chatStream(
        msg,
        history,
        (delta) => {
          accumulated += delta
          setMessages(prev => prev.map(m => m.id === placeholderId ? { ...m, content: accumulated } : m))
        },
        () => {
          setMessages(prev => prev.map(m => m.id === placeholderId ? { ...m, streaming: false, id: undefined } : m))
          setLoading(false)
        }
      )
    } catch {
      setMessages(prev => prev.map(m => m.id === placeholderId ? { ...m, content: 'Sorry, I encountered an error. Please check your NVIDIA_API_KEY in the .env file.', streaming: false, id: undefined } : m))
      setLoading(false)
    }
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-obsidian-600 glass">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-emerald-500 flex items-center justify-center">
              <Bot size={18} className="text-white" />
            </div>
            <div>
              <div className="font-semibold text-slate-200 flex items-center gap-2">FinanceAI Advisor <Sparkles size={13} className="text-violet-400" /></div>
              <div className="text-xs text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                bytedance/seed-oss-36b-instruct · NVIDIA API
              </div>
            </div>
          </div>
          <button onClick={() => setMessages([{ role: 'assistant', content: "Hello! I'm FinanceAI. How can I help you today?" }])} className="flex items-center gap-2 text-xs text-slate-500 hover:text-slate-300 py-1.5 px-3 rounded-xl hover:bg-obsidian-700 transition-all">
            <RefreshCw size={13} /> Clear
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.map((msg, i) => <MessageBubble key={msg.id || i} msg={msg} />)}
          <div ref={bottomRef} />
        </div>

        {/* Suggested Prompts */}
        {messages.length <= 1 && (
          <div className="px-6 pb-3">
            <p className="text-xs text-slate-500 mb-2 font-medium">Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED.map(p => (
                <button key={p} onClick={() => sendMessage(p)} className="text-xs px-3 py-1.5 bg-obsidian-700 border border-obsidian-500 rounded-xl text-slate-400 hover:text-slate-200 hover:border-obsidian-400 transition-all">
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="px-6 pb-6 pt-2">
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
              placeholder="Ask about your finances... (Enter to send)"
              rows={1}
              className="input-field flex-1 resize-none py-3 leading-relaxed"
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
            <button onClick={() => sendMessage()} disabled={!input.trim() || loading}
              className="w-11 h-11 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-all flex-shrink-0">
              <Send size={16} className="text-obsidian-900" />
            </button>
          </div>
          <p className="text-xs text-slate-600 mt-2 text-center">Powered by bytedance/seed-oss-36b-instruct via NVIDIA API · Based on your real financial data</p>
        </div>
      </div>

      {/* Insights Panel */}
      <div className="w-72 border-l border-obsidian-600 p-5 overflow-y-auto hidden xl:block flex-shrink-0">
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb size={15} className="text-amber-400" />
          <h3 className="text-sm font-semibold text-slate-300">AI Insights</h3>
        </div>
        <div className="space-y-3">
          {insights.map((insight, i) => (
            <div key={i}
              className={`p-3 rounded-xl border text-xs cursor-pointer hover:opacity-80 transition-opacity ${insight.type === 'success' ? 'bg-emerald-500/8 border-emerald-500/20' : insight.type === 'warning' ? 'bg-amber-500/8 border-amber-500/20' : 'bg-obsidian-700 border-obsidian-500'}`}
              onClick={() => sendMessage(insight.message)}>
              <div className="flex items-center gap-1.5 mb-1"><span>{insight.icon}</span><span className="font-semibold text-slate-200">{insight.title}</span></div>
              <p className="text-slate-400 leading-relaxed">{insight.message}</p>
              <p className="text-slate-600 mt-1.5">Click to ask →</p>
            </div>
          ))}
        </div>
        <div className="mt-6 p-3 rounded-xl bg-obsidian-700 border border-obsidian-500">
          <p className="text-xs text-slate-500 leading-relaxed">
            <span className="text-violet-400 font-medium">Setup:</span> Add your NVIDIA API key to the <code className="bg-obsidian-600 px-1 rounded">.env</code> file in the project root.
          </p>
        </div>
      </div>
    </div>
  )
}
