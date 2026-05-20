import React, { useState, useEffect } from 'react'
import { transactionsAPI } from '../utils/api'
import { formatCurrency, formatDate, getCategoryIcon, getCategoryColor } from '../utils/format'
import { Plus, Trash2, Search } from 'lucide-react'
import toast from 'react-hot-toast'

const CATEGORIES = ['Food & Dining','Transportation','Shopping','Entertainment','Bills & Utilities','Health & Medical','Education','Travel','Income','Investment','Other']

export default function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [form, setForm] = useState({ title: '', amount: '', type: 'expense', category: 'Food & Dining', date: new Date().toISOString().split('T')[0], notes: '' })

  const load = () => transactionsAPI.getAll().then(r => { setTransactions(r.data); setLoading(false) })
  useEffect(() => { load() }, [])

  const handleSubmit = async () => {
    if (!form.title || !form.amount) return toast.error('Please fill required fields')
    try {
      await transactionsAPI.create({ ...form, amount: parseFloat(form.amount), date: new Date(form.date).toISOString() })
      toast.success('Transaction added!')
      setShowForm(false)
      setForm({ title: '', amount: '', type: 'expense', category: 'Food & Dining', date: new Date().toISOString().split('T')[0], notes: '' })
      load()
    } catch { toast.error('Failed to add transaction') }
  }

  const handleDelete = async (id) => {
    try {
      await transactionsAPI.delete(id)
      toast.success('Deleted')
      setTransactions(prev => prev.filter(t => t.id !== id))
    } catch { toast.error('Failed to delete') }
  }

  const filtered = transactions.filter(t =>
    (filterType === 'all' || t.type === filterType) &&
    (t.title.toLowerCase().includes(search.toLowerCase()) || t.category.toLowerCase().includes(search.toLowerCase()))
  )

  const totalIncome = transactions.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0)
  const totalExpense = transactions.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0)

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Transactions</h1>
          <p className="text-slate-500 text-sm mt-1">{transactions.length} total transactions</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2"><Plus size={16} /> Add Transaction</button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[['Total Income', totalIncome, 'text-emerald-400'], ['Total Expenses', totalExpense, 'text-rose-400'], ['Net Balance', totalIncome - totalExpense, totalIncome - totalExpense >= 0 ? 'text-emerald-400' : 'text-rose-400']].map(([label, val, color]) => (
          <div key={label} className="card p-4">
            <div className="text-xs text-slate-500 mb-1">{label}</div>
            <div className={`font-mono text-lg font-bold ${color}`}>{formatCurrency(val)}</div>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..." className="input-field pl-9" />
        </div>
        <div className="flex items-center gap-1 bg-obsidian-700 rounded-xl p-1">
          {['all','income','expense'].map(t => (
            <button key={t} onClick={() => setFilterType(t)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${filterType === t ? 'bg-obsidian-500 text-slate-200' : 'text-slate-500 hover:text-slate-300'}`}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {showForm && (
        <div className="card p-5 border-emerald-500/20">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">New Transaction</h3>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-slate-500 mb-1 block">Title *</label><input value={form.title} onChange={e => setForm({...form, title: e.target.value})} placeholder="e.g. Grocery Shopping" className="input-field" /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">Amount (₹) *</label><input type="number" value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} placeholder="0" className="input-field" /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">Type</label><select value={form.type} onChange={e => setForm({...form, type: e.target.value})} className="input-field"><option value="expense">Expense</option><option value="income">Income</option></select></div>
            <div><label className="text-xs text-slate-500 mb-1 block">Category</label><select value={form.category} onChange={e => setForm({...form, category: e.target.value})} className="input-field">{CATEGORIES.map(c => <option key={c}>{c}</option>)}</select></div>
            <div><label className="text-xs text-slate-500 mb-1 block">Date</label><input type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})} className="input-field" /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">Notes</label><input value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} placeholder="Optional" className="input-field" /></div>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={handleSubmit} className="btn-primary">Add Transaction</button>
            <button onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      <div className="card overflow-hidden">
        <div className="divide-y divide-obsidian-600">
          {loading ? [...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 p-4">
              <div className="w-10 h-10 rounded-xl shimmer" />
              <div className="flex-1 space-y-2"><div className="h-3 shimmer rounded w-1/3" /><div className="h-2 shimmer rounded w-1/4" /></div>
              <div className="h-4 shimmer rounded w-20" />
            </div>
          )) : filtered.length === 0 ? (
            <div className="text-center py-12 text-slate-500"><div className="text-3xl mb-2">💸</div><p className="text-sm">No transactions found</p></div>
          ) : filtered.map(t => (
            <div key={t.id} className="flex items-center gap-4 p-4 hover:bg-obsidian-700/30 transition-colors group">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0" style={{ background: getCategoryColor(t.category) + '20' }}>{getCategoryIcon(t.category)}</div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-slate-200 truncate">{t.title}</div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-slate-500">{formatDate(t.date)}</span>
                  <span className="w-1 h-1 rounded-full bg-obsidian-500" />
                  <span className="text-xs" style={{ color: getCategoryColor(t.category) }}>{t.category}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`font-mono text-sm font-semibold ${t.type === 'income' ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                </span>
                <button onClick={() => handleDelete(t.id)} className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-rose-500/10 text-slate-600 hover:text-rose-400 transition-all"><Trash2 size={14} /></button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
