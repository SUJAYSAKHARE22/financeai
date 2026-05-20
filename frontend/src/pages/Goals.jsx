import React, { useState, useEffect } from 'react'
import { goalsAPI } from '../utils/api'
import { formatCurrency, formatDate } from '../utils/format'
import { Plus, Trash2, Target, Calendar, TrendingUp } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Goals() {
  const [goals, setGoals] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [updatingId, setUpdatingId] = useState(null)
  const [updateAmount, setUpdateAmount] = useState('')
  const [form, setForm] = useState({ title: '', target_amount: '', current_amount: '0', deadline: '', description: '' })

  const load = () => goalsAPI.getAll().then(r => { setGoals(r.data); setLoading(false) })
  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    if (!form.title || !form.target_amount) return toast.error('Fill required fields')
    try {
      await goalsAPI.create({ ...form, target_amount: parseFloat(form.target_amount), current_amount: parseFloat(form.current_amount) || 0, deadline: form.deadline ? new Date(form.deadline).toISOString() : null })
      toast.success('Goal created!'); setShowForm(false); setForm({ title: '', target_amount: '', current_amount: '0', deadline: '', description: '' }); load()
    } catch { toast.error('Failed to create goal') }
  }

  const handleUpdateProgress = async (id) => {
    try {
      await goalsAPI.updateProgress(id, parseFloat(updateAmount))
      toast.success('Progress updated!'); setUpdatingId(null); load()
    } catch { toast.error('Failed to update') }
  }

  const handleDelete = async (id) => {
    try {
      await goalsAPI.delete(id); toast.success('Deleted'); setGoals(prev => prev.filter(g => g.id !== id))
    } catch { toast.error('Failed to delete') }
  }

  const totalTargeted = goals.reduce((s, g) => s + g.target_amount, 0)
  const totalSaved = goals.reduce((s, g) => s + g.current_amount, 0)

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-100">Financial Goals</h1><p className="text-slate-500 text-sm mt-1">{goals.filter(g => g.current_amount >= g.target_amount).length}/{goals.length} goals achieved</p></div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2"><Plus size={16} /> New Goal</button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[['Total Targeted', totalTargeted, 'text-slate-200'], ['Total Saved', totalSaved, 'text-emerald-400'], ['Overall', totalTargeted > 0 ? `${((totalSaved / totalTargeted) * 100).toFixed(1)}%` : '0%', 'text-violet-400']].map(([l, v, c]) => (
          <div key={l} className="card p-4"><div className="text-xs text-slate-500 mb-1">{l}</div><div className={`font-mono text-lg font-bold ${c}`}>{typeof v === 'string' ? v : formatCurrency(v)}</div></div>
        ))}
      </div>

      {showForm && (
        <div className="card p-5 border-violet-500/20">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">New Goal</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2"><label className="text-xs text-slate-500 mb-1 block">Title *</label><input value={form.title} onChange={e => setForm({...form, title: e.target.value})} placeholder="e.g. Emergency Fund" className="input-field" /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">Target Amount (₹) *</label><input type="number" value={form.target_amount} onChange={e => setForm({...form, target_amount: e.target.value})} placeholder="100000" className="input-field" /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">Current Amount (₹)</label><input type="number" value={form.current_amount} onChange={e => setForm({...form, current_amount: e.target.value})} placeholder="0" className="input-field" /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">Deadline</label><input type="date" value={form.deadline} onChange={e => setForm({...form, deadline: e.target.value})} className="input-field" /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">Description</label><input value={form.description} onChange={e => setForm({...form, description: e.target.value})} placeholder="What's this for?" className="input-field" /></div>
          </div>
          <div className="flex gap-2 mt-4"><button onClick={handleCreate} className="btn-primary">Create Goal</button><button onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button></div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading ? [...Array(3)].map((_, i) => <div key={i} className="card p-5 h-48 shimmer" />) :
          goals.length === 0 ? (
            <div className="col-span-2 text-center py-16 text-slate-500"><div className="text-4xl mb-3">🎯</div><p className="text-sm">No goals yet. Set your first!</p></div>
          ) : goals.map(g => {
            const pct = Math.min((g.current_amount / g.target_amount) * 100, 100)
            const completed = pct >= 100
            const daysLeft = g.deadline ? Math.ceil((new Date(g.deadline) - new Date()) / (1000 * 60 * 60 * 24)) : null
            return (
              <div key={g.id} className={`card p-5 border ${completed ? 'border-emerald-500/30' : 'border-obsidian-600'}`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${completed ? 'bg-emerald-500/20' : 'bg-violet-500/10'}`}>
                      {completed ? '✅' : <Target size={18} className="text-violet-400" />}
                    </div>
                    <div>
                      <div className="font-semibold text-slate-200">{g.title}</div>
                      {g.description && <div className="text-xs text-slate-500 mt-0.5">{g.description}</div>}
                    </div>
                  </div>
                  <button onClick={() => handleDelete(g.id)} className="p-1.5 rounded-lg hover:bg-rose-500/10 text-slate-600 hover:text-rose-400 transition-all"><Trash2 size={13} /></button>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Saved: <span className="font-mono font-semibold text-slate-200">{formatCurrency(g.current_amount)}</span></span>
                    <span className="text-slate-400">Goal: <span className="font-mono font-semibold text-slate-200">{formatCurrency(g.target_amount)}</span></span>
                  </div>
                  <div className="h-2.5 bg-obsidian-600 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: completed ? '#10b981' : 'linear-gradient(90deg, #8b5cf6, #10b981)' }} />
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className={`font-semibold ${completed ? 'text-emerald-400' : 'text-violet-400'}`}>{pct.toFixed(1)}%</span>
                    {daysLeft !== null && <span className={`flex items-center gap-1 ${daysLeft < 30 ? 'text-amber-400' : 'text-slate-500'}`}><Calendar size={11} />{daysLeft > 0 ? `${daysLeft} days left` : 'Past deadline'}</span>}
                  </div>
                </div>

                {!completed ? (
                  updatingId === g.id ? (
                    <div className="flex gap-2">
                      <input type="number" value={updateAmount} onChange={e => setUpdateAmount(e.target.value)} placeholder="New amount (₹)" className="input-field flex-1" />
                      <button onClick={() => handleUpdateProgress(g.id)} className="btn-primary px-3">Save</button>
                      <button onClick={() => setUpdatingId(null)} className="btn-secondary px-3">Cancel</button>
                    </div>
                  ) : (
                    <button onClick={() => { setUpdatingId(g.id); setUpdateAmount(g.current_amount) }} className="w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 hover:bg-violet-500/15 transition-all text-sm font-medium">
                      <TrendingUp size={14} /> Update Progress
                    </button>
                  )
                ) : (
                  <div className="text-center py-2 text-emerald-400 text-sm font-semibold">🎉 Goal Achieved!</div>
                )}
              </div>
            )
          })}
      </div>
    </div>
  )
}
