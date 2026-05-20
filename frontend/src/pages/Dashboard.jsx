import React, { useState, useEffect } from 'react'
import { dashboardAPI, aiAPI } from '../utils/api'
import { formatCurrency, formatShortDate, getCategoryIcon, getCategoryColor } from '../utils/format'
import { TrendingUp, TrendingDown, Wallet, PiggyBank, Bell, ArrowRight, Lightbulb } from 'lucide-react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [insights, setInsights] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([dashboardAPI.getSummary(), aiAPI.getInsights()])
      .then(([d, i]) => { setData(d.data); setInsights(i.data.insights) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center space-y-3">
        <div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-500 text-sm">Loading your finances...</p>
      </div>
    </div>
  )

  const { summary, budget_health, goal_progress, recent_transactions, alerts } = data || {}
  const statCards = [
    { label: 'Total Income', value: summary?.total_income, color: 'text-emerald-400', border: 'border-emerald-500/20', icon: TrendingUp, bg: 'bg-emerald-500/10' },
    { label: 'Total Expenses', value: summary?.total_expense, color: 'text-rose-400', border: 'border-rose-500/20', icon: TrendingDown, bg: 'bg-rose-500/10' },
    { label: 'Net Savings', value: summary?.savings, color: 'text-violet-400', border: 'border-violet-500/20', icon: PiggyBank, bg: 'bg-violet-500/10' },
    { label: 'Savings Rate', value: `${summary?.savings_rate?.toFixed(1)}%`, color: 'text-amber-400', border: 'border-amber-500/20', icon: Wallet, bg: 'bg-amber-500/10', isStr: true },
  ]
  const pieData = Object.entries(summary?.category_spending || {}).map(([k, v]) => ({ name: k, value: v }))

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Financial Overview</h1>
          <p className="text-slate-500 text-sm mt-1">{new Date().toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}</p>
        </div>
        {alerts?.length > 0 && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium">
            <Bell size={14} />{alerts.length} Alert{alerts.length > 1 ? 's' : ''}
          </div>
        )}
      </div>

      {alerts?.map((a, i) => (
        <div key={i} className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm border ${a.type === 'danger' ? 'bg-rose-500/8 border-rose-500/20 text-rose-300' : 'bg-amber-500/8 border-amber-500/20 text-amber-300'}`}>
          {a.type === 'danger' ? '🚨' : '⚠️'} {a.message}
        </div>
      ))}

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {statCards.map(({ label, value, color, border, icon: Icon, bg, isStr }) => (
          <div key={label} className={`card p-5 border ${border}`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</span>
              <div className={`w-8 h-8 rounded-lg ${bg} flex items-center justify-center`}>
                <Icon size={15} className={color} />
              </div>
            </div>
            <div className={`font-mono text-xl font-bold ${color}`}>{isStr ? value : formatCurrency(value)}</div>
            <div className="text-xs text-slate-600 mt-1">This month</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Spending by Category</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" strokeWidth={0}>
                {pieData.map((e, i) => <Cell key={i} fill={getCategoryColor(e.name)} />)}
              </Pie>
              <Tooltip formatter={(v) => formatCurrency(v)} contentStyle={{ background: '#1a1a25', border: '1px solid #2e2e45', borderRadius: '10px', fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-2 mt-2">
            {pieData.slice(0, 4).map(item => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: getCategoryColor(item.name) }} />
                  <span className="text-slate-400">{getCategoryIcon(item.name)} {item.name}</span>
                </div>
                <span className="font-mono text-slate-300">{formatCurrency(item.value)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Budget Health</h3>
          <div className="space-y-4">
            {budget_health?.slice(0, 5).map(b => (
              <div key={b.category}>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-slate-400">{getCategoryIcon(b.category)} {b.category}</span>
                  <span className={`font-mono font-medium ${b.status === 'danger' ? 'text-rose-400' : b.status === 'warning' ? 'text-amber-400' : 'text-emerald-400'}`}>{b.percentage}%</span>
                </div>
                <div className="h-2 rounded-full bg-obsidian-600 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.min(b.percentage, 100)}%`, background: b.status === 'danger' ? '#f43f5e' : b.status === 'warning' ? '#f59e0b' : '#10b981' }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Goal Progress</h3>
          <div className="space-y-4">
            {goal_progress?.map(g => (
              <div key={g.id}>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-slate-300 font-medium">{g.title}</span>
                  <span className="text-violet-400 font-mono font-medium">{g.percentage}%</span>
                </div>
                <div className="h-2 rounded-full bg-obsidian-600 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700 bg-gradient-to-r from-violet-500 to-emerald-500" style={{ width: `${Math.min(g.percentage, 100)}%` }} />
                </div>
                <div className="flex justify-between text-xs text-slate-600 mt-1">
                  <span>{formatCurrency(g.current)}</span><span>{formatCurrency(g.target)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-300">Recent Transactions</h3>
            <a href="/transactions" className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1">View all <ArrowRight size={12} /></a>
          </div>
          <div className="space-y-3">
            {recent_transactions?.map(t => (
              <div key={t.id} className="flex items-center justify-between py-2 border-b border-obsidian-600 last:border-0">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-obsidian-700 flex items-center justify-center text-sm">{getCategoryIcon(t.category)}</div>
                  <div>
                    <div className="text-sm font-medium text-slate-200">{t.title}</div>
                    <div className="text-xs text-slate-500">{formatShortDate(t.date)}</div>
                  </div>
                </div>
                <span className={`font-mono text-sm font-semibold ${t.type === 'income' ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-5 border-violet-500/20">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb size={16} className="text-violet-400" />
            <h3 className="text-sm font-semibold text-slate-300">AI Insights</h3>
          </div>
          <div className="space-y-3">
            {insights.map((insight, i) => (
              <div key={i} className={`p-3 rounded-xl border text-sm ${insight.type === 'success' ? 'bg-emerald-500/8 border-emerald-500/20' : insight.type === 'warning' ? 'bg-amber-500/8 border-amber-500/20' : 'bg-obsidian-700 border-obsidian-500'}`}>
                <div className="flex items-center gap-2 mb-1">
                  <span>{insight.icon}</span>
                  <span className="font-semibold text-slate-200">{insight.title}</span>
                </div>
                <p className="text-slate-400 text-xs leading-relaxed">{insight.message}</p>
              </div>
            ))}
          </div>
          <a href="/ai-advisor" className="mt-4 flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 hover:bg-violet-500/15 transition-all text-sm font-medium">
            Chat with AI Advisor <ArrowRight size={14} />
          </a>
        </div>
      </div>
    </div>
  )
}
