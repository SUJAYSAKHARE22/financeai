import React, { useState, useEffect } from 'react'
import { budgetsAPI } from '../utils/api'
import { formatCurrency, getCategoryIcon, getCategoryColor } from '../utils/format'
import { Plus, Trash2, Edit2, Check, X } from 'lucide-react'
import toast from 'react-hot-toast'

const CATEGORIES = ['Food & Dining','Transportation','Shopping','Entertainment','Bills & Utilities','Health & Medical','Education','Travel','Investment','Other']

export default function Budgets() {
  const [budgets, setBudgets] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editValue, setEditValue] = useState('')
  const [form, setForm] = useState({ category: 'Food & Dining', limit: '' })

  const now = new Date()
  const load = () => budgetsAPI.getAll().then(r => { setBudgets(r.data); setLoading(false) })
  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    if (!form.limit) return toast.error('Enter a budget limit')
    try {
      await budgetsAPI.create({ ...form, limit: parseFloat(form.limit), month: now.getMonth() + 1, year: now.getFullYear() })
      toast.success('Budget created!'); setShowForm(false); setForm({ category: 'Food & Dining', limit: '' }); load()
    } catch { toast.error('Failed to create budget') }
  }

  const handleUpdate = async (id) => {
    try {
      await budgetsAPI.update(id, parseFloat(editValue))
      toast.success('Updated!'); setEditingId(null); load()
    } catch { toast.error('Failed to update') }
  }

  const handleDelete = async (id) => {
    try {
      await budgetsAPI.delete(id)
      toast.success('Deleted'); setBudgets(prev => prev.filter(b => b.id !== id))
    } catch { toast.error('Failed to delete') }
  }

  const totalBudgeted = budgets.reduce((s, b) => s + b.limit, 0)
  const totalSpent = budgets.reduce((s, b) => s + b.spent, 0)

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-100">Budgets</h1><p className="text-slate-500 text-sm mt-1">{now.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}</p></div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2"><Plus size={16} /> New Budget</button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[['Total Budgeted', totalBudgeted, 'text-slate-200'], ['Total Spent', totalSpent, 'text-rose-400'], ['Remaining', totalBudgeted - totalSpent, (totalBudgeted - totalSpent) >= 0 ? 'text-emerald-400' : 'text-rose-400']].map(([l, v, c]) => (
          <div key={l} className="card p-4"><div className="text-xs text-slate-500 mb-1">{l}</div><div className={`font-mono text-lg font-bold ${c}`}>{formatCurrency(v)}</div></div>
        ))}
      </div>

      {totalBudgeted > 0 && (
        <div className="card p-5">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-slate-300">Overall Usage</span>
            <span className="text-sm font-mono text-slate-400">{((totalSpent / totalBudgeted) * 100).toFixed(1)}%</span>
          </div>
          <div className="h-3 bg-obsidian-600 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.min((totalSpent / totalBudgeted) * 100, 100)}%`, background: (totalSpent / totalBudgeted) > 0.9 ? '#f43f5e' : (totalSpent / totalBudgeted) > 0.7 ? '#f59e0b' : '#10b981' }} />
          </div>
        </div>
      )}

      {showForm && (
        <div className="card p-5 border-emerald-500/20">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Create Budget</h3>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-slate-500 mb-1 block">Category</label><select value={form.category} onChange={e => setForm({...form, category: e.target.value})} className="input-field">{CATEGORIES.map(c => <option key={c}>{c}</option>)}</select></div>
            <div><label className="text-xs text-slate-500 mb-1 block">Monthly Limit (₹)</label><input type="number" value={form.limit} onChange={e => setForm({...form, limit: e.target.value})} placeholder="5000" className="input-field" /></div>
          </div>
          <div className="flex gap-2 mt-4"><button onClick={handleCreate} className="btn-primary">Create</button><button onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button></div>
        </div>
      )}

      <div className="space-y-4">
        {loading ? [...Array(4)].map((_, i) => <div key={i} className="card p-5 h-28 shimmer" />) :
          budgets.length === 0 ? (
            <div className="text-center py-16 text-slate-500"><div className="text-4xl mb-3">📊</div><p className="text-sm">No budgets yet. Create your first!</p></div>
          ) : budgets.map(b => {
            const pct = Math.min((b.spent / b.limit) * 100, 100)
            const status = pct >= 90 ? 'danger' : pct >= 70 ? 'warning' : 'good'
            const barColor = status === 'danger' ? '#f43f5e' : status === 'warning' ? '#f59e0b' : '#10b981'
            const remaining = b.limit - b.spent
            return (
              <div key={b.id} className={`card p-5 border transition-all ${status === 'danger' ? 'border-rose-500/30' : status === 'warning' ? 'border-amber-500/20' : 'border-obsidian-600'}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl" style={{ background: getCategoryColor(b.category) + '20' }}>{getCategoryIcon(b.category)}</div>
                    <div>
                      <div className="font-medium text-slate-200">{b.category}</div>
                      <div className={`text-xs mt-0.5 ${status === 'danger' ? 'text-rose-400' : status === 'warning' ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {status === 'danger' ? '⚠️ Over budget' : status === 'warning' ? '⚡ Approaching limit' : '✓ On track'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {editingId === b.id ? (
                      <>
                        <input type="number" value={editValue} onChange={e => setEditValue(e.target.value)} className="input-field w-28 text-right" />
                        <button onClick={() => handleUpdate(b.id)} className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400"><Check size={14} /></button>
                        <button onClick={() => setEditingId(null)} className="p-1.5 rounded-lg bg-obsidian-600 text-slate-400"><X size={14} /></button>
                      </>
                    ) : (
                      <>
                        <button onClick={() => { setEditingId(b.id); setEditValue(b.limit) }} className="p-1.5 rounded-lg hover:bg-obsidian-600 text-slate-500 hover:text-slate-300"><Edit2 size={14} /></button>
                        <button onClick={() => handleDelete(b.id)} className="p-1.5 rounded-lg hover:bg-rose-500/10 text-slate-500 hover:text-rose-400"><Trash2 size={14} /></button>
                      </>
                    )}
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Spent: <span className="font-mono font-semibold text-slate-200">{formatCurrency(b.spent)}</span></span>
                    <span className="text-slate-400">Limit: <span className="font-mono font-semibold text-slate-200">{formatCurrency(b.limit)}</span></span>
                  </div>
                  <div className="h-2.5 bg-obsidian-600 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: barColor }} />
                  </div>
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>{pct.toFixed(1)}% used</span>
                    <span className={remaining >= 0 ? 'text-emerald-400' : 'text-rose-400'}>{remaining >= 0 ? `${formatCurrency(remaining)} left` : `${formatCurrency(Math.abs(remaining))} over`}</span>
                  </div>
                </div>
              </div>
            )
          })}
      </div>
    </div>
  )
}
