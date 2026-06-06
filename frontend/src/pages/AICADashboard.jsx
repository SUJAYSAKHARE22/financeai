import React, { useState, useEffect } from 'react'
import { aicaAPI } from '../utils/aica_api'
import { formatCurrency } from '../utils/format'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import {
  FileText, TrendingUp, Calculator, BookOpen,
  Download, RefreshCw, AlertCircle, CheckCircle,
  ChevronRight, IndianRupee, Shield, Briefcase
} from 'lucide-react'
import AICAChat from '../components/AICAChat'
import toast from 'react-hot-toast'

const REGIME_COLORS = { old: '#8b5cf6', new: '#10b981' }

const CATEGORY_COLORS = [
  '#10b981','#8b5cf6','#f59e0b','#3b82f6','#ec4899',
  '#6366f1','#f97316','#14b8a6','#84cc16','#ef4444',
]

function StatCard({ label, value, sub, icon: Icon, color, border }) {
  return (
    <div className={`card p-5 border ${border || 'border-obsidian-600'}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</span>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center`} style={{ background: color + '20' }}>
          <Icon size={15} style={{ color }} />
        </div>
      </div>
      <div className="font-mono text-xl font-bold" style={{ color }}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  )
}

export default function AICADashboard() {
  const [overview, setOverview] = useState(null)
  const [taxData, setTaxData] = useState(null)
  const [statements, setStatements] = useState(null)
  const [loading, setLoading] = useState(true)
  const [regime, setRegime] = useState('new')
  const [activeTab, setActiveTab] = useState('overview')
  const [classifying, setClassifying] = useState(false)
  const [downloading, setDownloading] = useState(false)
  
  const [profile, setProfile] = useState(null)
  const [profileSaving, setProfileSaving] = useState(false)
  const [generatingDoc, setGeneratingDoc] = useState(null)

  const load = async (r = regime) => {
    setLoading(true)
    try {
      const [ov, tx, st, prof] = await Promise.all([
        aicaAPI.getOverview(r),
        aicaAPI.getTaxSummary(r),
        aicaAPI.getFinancialStatements({ period: 'monthly', regime: r }),
        aicaAPI.getProfile(),
      ])
      setOverview(ov.data)
      setTaxData(tx.data)
      setStatements(st.data)
      setProfile(prof.data)
    } catch (e) {
      toast.error('Failed to load AI-CA data')
    } finally {
      setLoading(false)
    }
  }

  const handleProfileChange = (key, value) => {
    setProfile(prev => ({ ...prev, [key]: value }))
  }

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setProfileSaving(true)
    try {
      await aicaAPI.saveProfile(profile)
      toast.success('Taxpayer profile updated!')
    } catch {
      toast.error('Failed to save profile')
    } finally {
      setProfileSaving(false)
    }
  }

  const downloadITRDoc = async (type) => {
    setGeneratingDoc(type)
    const fy = taxComp.financial_year || '2024-25'
    try {
      if (type === 'json') {
        await aicaAPI.downloadITRJson(profile, regime, fy)
        toast.success('Ready-to-file ITR JSON generated!')
      } else if (type === 'pdf') {
        await aicaAPI.downloadITRPdf(profile, regime, fy)
        toast.success('Official ITR-1 Sahaj Form PDF downloaded!')
      } else if (type === 'form16') {
        await aicaAPI.downloadForm16(profile, regime, fy)
        toast.success('Form 16 Tax Summary PDF downloaded!')
      } else if (type === 'form26as') {
        await aicaAPI.downloadForm26as(profile, regime, fy)
        toast.success('Form 26AS TDS Credit PDF downloaded!')
      }
    } catch (e) {
      console.error(e)
      toast.error(`Failed to generate ${type.toUpperCase()}`)
    } finally {
      setGeneratingDoc(null)
    }
  }

  const sumSalaries = (st) => {
    const pl = st?.profit_loss || {}
    return (pl.income_breakdown?.salary || 0)
  }

  const sumInterest = (st) => {
    const pl = st?.profit_loss || {}
    return (pl.income_breakdown?.interest_income || 0)
  }

  useEffect(() => { load() }, [])

  const handleRegimeChange = (r) => {
    setRegime(r)
    load(r)
  }

  const handleClassify = async () => {
    setClassifying(true)
    try {
      const res = await aicaAPI.classify(null, true)
      toast.success(`Classified ${res.data.total} transactions (${res.data.ai_classified} via AI)`)
      load()
    } catch { toast.error('Classification failed') }
    finally { setClassifying(false) }
  }

  const handleDownload = async (format) => {
    setDownloading(true)
    const fy = taxComp.financial_year || '2024-25'
    try {
      if (format === 'pdf') await aicaAPI.downloadPdf('full', 'monthly', regime, fy)
      else await aicaAPI.downloadExcel('full', 'monthly', regime, fy)
      toast.success(`${format.toUpperCase()} downloaded!`)
    } catch (e) {
      console.error(e)
      toast.error('Download failed')
    } finally {
      setDownloading(false)
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center space-y-3">
        <div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-500 text-sm">Analyzing your finances...</p>
      </div>
    </div>
  )

  const tax = overview?.tax_snapshot || {}
  const deductions = overview?.deduction_snapshot || {}
  const flags = overview?.expense_flags || {}
  const recs = overview?.recommendations || []
  const catDist = overview?.category_distribution || {}
  const topExpenses = overview?.top_expense_categories || {}
  const pl = statements?.profit_loss || {}
  const taxComp = taxData?.tax_computation || {}

  const pieData = Object.entries(catDist).map(([k, v]) => ({ name: k.replace(/_/g, ' '), value: v }))
  const expenseBarData = Object.entries(topExpenses).map(([k, v]) => ({
    name: k.replace(/_/g, ' ').slice(0, 12), amount: v.total, deductible: v.deductible
  }))

  const tabs = [
    { id: 'overview', label: 'Overview', icon: TrendingUp },
    { id: 'tax', label: 'Tax', icon: Calculator },
    { id: 'statements', label: 'Statements', icon: BookOpen },
    { id: 'itr', label: 'E-Filing & Docs', icon: FileText },
    { id: 'chat', label: 'AI-CA Chat', icon: Shield },
  ]

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-violet-500 flex items-center justify-center">
              <Shield size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100">AI-CA</h1>
              <p className="text-slate-500 text-sm">AI Chartered Accountant · FY 2024-25</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Regime toggle */}
          <div className="flex items-center gap-1 bg-obsidian-700 rounded-xl p-1">
            {['new', 'old'].map(r => (
              <button key={r} onClick={() => handleRegimeChange(r)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${regime === r ? 'bg-emerald-500 text-obsidian-900' : 'text-slate-400 hover:text-slate-200'}`}>
                {r} regime
              </button>
            ))}
          </div>

          <button onClick={handleClassify} disabled={classifying}
            className="flex items-center gap-2 text-xs px-4 py-2 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 hover:bg-violet-500/15 transition-all disabled:opacity-50">
            <RefreshCw size={13} className={classifying ? 'animate-spin' : ''} />
            {classifying ? 'Classifying...' : 'Re-classify'}
          </button>

          <button onClick={() => handleDownload('pdf')} disabled={downloading}
            className="flex items-center gap-2 text-xs px-4 py-2 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/15 transition-all disabled:opacity-50">
            <Download size={13} /> PDF
          </button>

          <button onClick={() => handleDownload('excel')} disabled={downloading}
            className="flex items-center gap-2 text-xs px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/15 transition-all disabled:opacity-50">
            <Download size={13} /> Excel
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-obsidian-800 border border-obsidian-600 rounded-2xl p-1 w-fit">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${activeTab === id ? 'bg-obsidian-600 text-slate-200' : 'text-slate-500 hover:text-slate-300'}`}>
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ─────────────────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stat row */}
          <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard label="Gross Income" value={formatCurrency(tax.gross_income)} sub="This month tracked" icon={TrendingUp} color="#10b981" border="border-emerald-500/20" />
            <StatCard label="Tax Liability" value={formatCurrency(tax.total_tax_liability)} sub={`${tax.effective_tax_rate}% effective rate`} icon={Calculator} color="#f43f5e" border="border-rose-500/20" />
            <StatCard label="Taxable Income" value={formatCurrency(tax.taxable_income)} sub={`after ₹${(taxComp.total_deductions || 0).toLocaleString('en-IN')} deductions`} icon={IndianRupee} color="#f59e0b" border="border-amber-500/20" />
            <StatCard label="Net Tax Payable" value={formatCurrency(tax.net_tax_payable)} sub="after TDS credit" icon={FileText} color="#8b5cf6" border="border-violet-500/20" />
          </div>

          {/* Second row */}
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Deductible Expenses" value={formatCurrency(flags.deductible_total)} sub="Identified for deduction" icon={CheckCircle} color="#10b981" />
            <StatCard label="Business Expenses" value={formatCurrency(flags.business_related_total)} sub="Business-related spend" icon={Briefcase} color="#6366f1" />
            <StatCard label="GST-Applicable" value={formatCurrency(flags.gst_applicable_total)} sub="GST transactions" icon={Shield} color="#f59e0b" />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Category Distribution */}
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Transaction Category Mix</h3>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} dataKey="value" strokeWidth={0}>
                    {pieData.map((_, i) => <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(v, n) => [v + ' txns', n]} contentStyle={{ background: '#1a1a25', border: '1px solid #2e2e45', borderRadius: '10px', fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-2 gap-1 mt-2">
                {pieData.slice(0, 6).map((item, i) => (
                  <div key={item.name} className="flex items-center gap-1.5 text-xs">
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }} />
                    <span className="text-slate-400 truncate capitalize">{item.name}</span>
                    <span className="text-slate-500 ml-auto">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Expenses Bar */}
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Top Expense Categories</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={expenseBarData} layout="vertical" margin={{ left: 0, right: 20 }}>
                  <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} width={90} />
                  <Tooltip formatter={v => formatCurrency(v)} contentStyle={{ background: '#1a1a25', border: '1px solid #2e2e45', borderRadius: '8px', fontSize: '11px' }} />
                  <Bar dataKey="amount" fill="#8b5cf6" radius={[0, 4, 4, 0]} name="Total" />
                  <Bar dataKey="deductible" fill="#10b981" radius={[0, 4, 4, 0]} name="Deductible" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Recommendations */}
            <div className="card p-5 border-emerald-500/20">
              <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                <AlertCircle size={14} className="text-amber-400" /> Tax Recommendations
              </h3>
              <div className="space-y-3">
                {recs.map((rec, i) => (
                  <div key={i} className="flex gap-2 text-xs p-3 rounded-xl bg-obsidian-700 border border-obsidian-500">
                    <span className="text-emerald-400 mt-0.5 flex-shrink-0">•</span>
                    <span className="text-slate-400 leading-relaxed">{rec}</span>
                  </div>
                ))}
              </div>
              <button onClick={() => setActiveTab('chat')}
                className="mt-4 w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium hover:bg-emerald-500/15 transition-all">
                Ask AI-CA for more advice <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── TAX TAB ──────────────────────────────────────────────────────── */}
      {activeTab === 'tax' && taxComp && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Tax Computation */}
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Tax Computation — {regime.toUpperCase()} Regime</h3>
              <div className="space-y-3">
                {[
                  ['Gross Income', taxComp.gross_income, 'text-emerald-400'],
                  ['(-) Deductions', taxComp.total_deductions, 'text-slate-400'],
                  ['= Taxable Income', taxComp.taxable_income, 'text-amber-400'],
                  ['Tax (before cess)', taxComp.tax_before_cess, 'text-slate-300'],
                  ['Education Cess (4%)', taxComp.education_cess, 'text-slate-300'],
                  ['Total Tax Liability', taxComp.total_tax_liability, 'text-rose-400'],
                  ['(-) TDS Paid', taxComp.tds_already_paid, 'text-slate-400'],
                  ['Net Tax Payable', taxComp.net_tax_payable, 'text-rose-400 font-bold'],
                ].map(([label, val, cls]) => (
                  <div key={label} className="flex items-center justify-between py-2 border-b border-obsidian-600 last:border-0">
                    <span className="text-xs text-slate-400">{label}</span>
                    <span className={`font-mono text-sm ${cls}`}>{formatCurrency(val)}</span>
                  </div>
                ))}
              </div>
              <div className="mt-4 p-3 rounded-xl bg-obsidian-700 border border-obsidian-500 text-xs text-slate-500">
                Effective Tax Rate: <span className="text-amber-400 font-mono font-semibold">{taxComp.effective_tax_rate}%</span>
                <span className="mx-2">·</span>
                FY: <span className="text-slate-300">{taxComp.financial_year}</span>
              </div>
            </div>

            {/* Deductions */}
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Deduction Breakdown</h3>
              <div className="space-y-4">
                {[
                  { label: 'Standard Deduction', used: taxComp.deduction_breakdown?.standard_deduction, limit: regime === 'new' ? 75000 : 50000, color: '#10b981' },
                  { label: 'Section 80C', used: taxComp.deduction_breakdown?.section_80c, limit: 150000, color: '#8b5cf6' },
                  { label: 'Section 80D', used: taxComp.deduction_breakdown?.section_80d, limit: 25000, color: '#3b82f6' },
                  { label: 'HRA Exemption', used: taxComp.deduction_breakdown?.hra_exemption || 0, limit: null, color: '#f59e0b' },
                ].map(({ label, used, limit, color }) => {
                  const pct = limit ? Math.min((used / limit) * 100, 100) : 0
                  return (
                    <div key={label}>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-slate-400">{label}</span>
                        <span className="font-mono" style={{ color }}>{formatCurrency(used)}{limit ? ` / ₹${(limit/1000).toFixed(0)}k` : ''}</span>
                      </div>
                      {limit && (
                        <div className="h-2 rounded-full bg-obsidian-600 overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color }} />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Slab breakdown */}
              {taxComp.slabs_applied?.length > 0 && (
                <div className="mt-5">
                  <h4 className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wider">Tax Slabs Applied</h4>
                  <div className="space-y-1">
                    {taxComp.slabs_applied.map((slab, i) => (
                      <div key={i} className="flex justify-between text-xs py-1.5 border-b border-obsidian-600 last:border-0">
                        {slab.note ? (
                          <span className="text-emerald-400">{slab.note}</span>
                        ) : (
                          <>
                            <span className="text-slate-500">{slab.slab} @ {slab.rate}</span>
                            <span className="font-mono text-slate-300">{formatCurrency(slab.tax)}</span>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Recommendations */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Personalized Tax Recommendations</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              {(taxData?.recommendations || []).map((rec, i) => (
                <div key={i} className="p-3 rounded-xl bg-obsidian-700 border border-obsidian-500 text-xs text-slate-400 leading-relaxed">
                  <span className="text-amber-400 mr-1.5">💡</span>{rec}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── STATEMENTS TAB ───────────────────────────────────────────────── */}
      {activeTab === 'statements' && statements && (
        <div className="space-y-6">
          {/* P&L */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Profit & Loss Statement — {statements.profit_loss?.period}</h3>
            <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-4">
              {[
                ['Total Income', statements.profit_loss?.total_income, 'text-emerald-400'],
                ['Total Expenses', statements.profit_loss?.total_expenses, 'text-rose-400'],
                ['Net Profit', statements.profit_loss?.net_profit, statements.profit_loss?.net_profit >= 0 ? 'text-emerald-400' : 'text-rose-400'],
                ['Profit Margin', `${statements.profit_loss?.profit_margin?.toFixed(1)}%`, 'text-violet-400'],
              ].map(([l, v, c]) => (
                <div key={l} className="card p-3">
                  <div className="text-xs text-slate-500 mb-1">{l}</div>
                  <div className={`font-mono font-bold ${c}`}>{typeof v === 'string' ? v : formatCurrency(v)}</div>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              {[
                ['Income Breakdown', statements.profit_loss?.income_breakdown, '#10b981'],
                ['Expense Breakdown', statements.profit_loss?.expense_breakdown, '#f43f5e'],
              ].map(([title, data, color]) => data && (
                <div key={title}>
                  <h4 className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">{title}</h4>
                  <div className="space-y-1.5">
                    {Object.entries(data).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-xs py-1.5 border-b border-obsidian-600 last:border-0">
                        <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                        <span className="font-mono" style={{ color }}>{formatCurrency(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cash Flow */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Cash Flow Summary</h3>
            <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
              {[
                ['Inflows', statements.cash_flow?.total_inflows, 'text-emerald-400'],
                ['Outflows', statements.cash_flow?.total_outflows, 'text-rose-400'],
                ['Net Cash Flow', statements.cash_flow?.net_cash_flow, statements.cash_flow?.net_cash_flow >= 0 ? 'text-emerald-400' : 'text-rose-400'],
                ['Closing Balance', statements.cash_flow?.closing_balance, 'text-violet-400'],
              ].map(([l, v, c]) => (
                <div key={l} className="card p-3">
                  <div className="text-xs text-slate-500 mb-1">{l}</div>
                  <div className={`font-mono font-bold ${c}`}>{formatCurrency(v)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Export buttons */}
          <div className="flex gap-3">
            <button onClick={() => handleDownload('pdf')} disabled={downloading}
              className="flex items-center gap-2 btn-primary">
              <Download size={15} /> Download PDF Report
            </button>
            <button onClick={() => handleDownload('excel')} disabled={downloading}
              className="flex items-center gap-2 btn-secondary">
              <Download size={15} /> Download Excel Report
            </button>
          </div>
        </div>
      )}

      {/* ── E-FILING & DOCUMENTS TAB ─────────────────────────────────────── */}
      {activeTab === 'itr' && profile && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 text-slate-100">
          {/* Left: Taxpayer Profile Form */}
          <div className="lg:col-span-7 card p-6 space-y-6 border border-obsidian-600 bg-obsidian-900">
            <div className="flex items-center gap-3 pb-3 border-b border-obsidian-700">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <FileText size={20} />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Taxpayer Profile Details</h3>
                <p className="text-slate-500 text-xs">Verify your official personal and banking records for e-filing</p>
              </div>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">First Name</label>
                  <input type="text" value={profile.first_name || ''} onChange={e => handleProfileChange('first_name', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">Last Name</label>
                  <input type="text" value={profile.last_name || ''} onChange={e => handleProfileChange('last_name', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">PAN (10 digits)</label>
                  <input type="text" value={profile.pan || ''} onChange={e => handleProfileChange('pan', e.target.value.toUpperCase())}
                    className="w-full font-mono text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required maxLength={10} />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">Aadhaar (12 digits)</label>
                  <input type="text" value={profile.aadhaar_no || ''} onChange={e => handleProfileChange('aadhaar_no', e.target.value)}
                    className="w-full font-mono text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required maxLength={19} />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">Date of Birth</label>
                  <input type="date" value={profile.dob || ''} onChange={e => handleProfileChange('dob', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">Email Address</label>
                  <input type="email" value={profile.email || ''} onChange={e => handleProfileChange('email', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">Mobile Number</label>
                  <input type="text" value={profile.mobile || ''} onChange={e => handleProfileChange('mobile', e.target.value)}
                    className="w-full font-mono text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required maxLength={10} />
                </div>
              </div>

              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Postal Address</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <input type="text" placeholder="Flat / Door / Block No." value={profile.address_flat || ''} onChange={e => handleProfileChange('address_flat', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                  <input type="text" placeholder="Premises / Building / Village" value={profile.address_premises || ''} onChange={e => handleProfileChange('address_premises', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <input type="text" placeholder="Road / Street" value={profile.address_road || ''} onChange={e => handleProfileChange('address_road', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                  <input type="text" placeholder="Area / Locality" value={profile.address_area || ''} onChange={e => handleProfileChange('address_area', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                  <input type="text" placeholder="City" value={profile.address_city || ''} onChange={e => handleProfileChange('address_city', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <input type="text" placeholder="State" value={profile.address_state || ''} onChange={e => handleProfileChange('address_state', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                  <input type="text" placeholder="PIN Code" value={profile.address_pin || ''} onChange={e => handleProfileChange('address_pin', e.target.value)}
                    className="w-full font-mono text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required maxLength={6} />
                  <select value={profile.employer_type || 'PRIVATE'} onChange={e => handleProfileChange('employer_type', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors">
                    <option value="PRIVATE">Private Sector Employee</option>
                    <option value="GOVT">Central/State Govt</option>
                    <option value="PSU">Public Sector Undertaking</option>
                    <option value="OTHERS">Others (Freelancers/Self-Employed)</option>
                  </select>
                </div>
              </div>

              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Primary Bank Account</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <input type="text" placeholder="Bank Name" value={profile.bank_name || ''} onChange={e => handleProfileChange('bank_name', e.target.value)}
                    className="w-full text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                  <input type="text" placeholder="Account Number" value={profile.bank_account_no || ''} onChange={e => handleProfileChange('bank_account_no', e.target.value)}
                    className="w-full font-mono text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                  <input type="text" placeholder="IFSC Code" value={profile.bank_ifsc || ''} onChange={e => handleProfileChange('bank_ifsc', e.target.value.toUpperCase())}
                    className="w-full font-mono text-xs bg-obsidian-800 border border-obsidian-600 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors" required />
                </div>
                <div className="flex items-center gap-2.5 pt-1">
                  <input type="checkbox" id="bank_refund" checked={profile.bank_refund_eligible || false} onChange={e => handleProfileChange('bank_refund_eligible', e.target.checked)}
                    className="rounded border-obsidian-600 bg-obsidian-800 text-emerald-500 focus:ring-emerald-500" />
                  <label htmlFor="bank_refund" className="text-xs text-slate-400 select-none">Select this bank account for Refund payout</label>
                </div>
              </div>

              <button type="submit" disabled={profileSaving}
                className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-obsidian-900 text-sm font-semibold transition-all shadow-lg disabled:opacity-50 flex items-center justify-center gap-2">
                {profileSaving ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" /> Saving...
                  </>
                ) : 'Save Profile Changes'}
              </button>
            </form>
          </div>

          {/* Right: ITR-1 Live Preview & Documents Download */}
          <div className="lg:col-span-5 space-y-6">
            {/* Live Document Preview */}
            <div className="card p-5 border border-emerald-500/20 bg-gradient-to-b from-obsidian-850 to-obsidian-900 space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-obsidian-700 pb-2">
                <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md uppercase tracking-wider">FORM ITR-1 LIVE PREVIEW</span>
                <span className="text-[10px] text-slate-500 font-semibold font-mono uppercase">AY 2025-26</span>
              </div>

              <div className="space-y-3 font-mono text-[11px] text-slate-300">
                <div className="bg-obsidian-900/60 p-3 rounded-xl border border-obsidian-700 space-y-1.5 shadow-inner">
                  <div className="flex justify-between"><span className="text-slate-500">Name:</span> <span className="font-bold text-slate-200">{profile.first_name || ''} {profile.last_name || ''}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">PAN:</span> <span className="font-bold text-amber-500">{profile.pan || ''}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Status:</span> <span>Resident Individual</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Filing Sec:</span> <span>139(1) - On Time</span></div>
                </div>

                <div className="space-y-2 pt-1">
                  <div className="flex justify-between border-b border-obsidian-750 pb-1.5">
                    <span className="text-slate-400">A. Gross Salary Income:</span>
                    <span className="text-emerald-400 font-semibold">{formatCurrency(sumSalaries(statements))}</span>
                  </div>
                  <div className="flex justify-between border-b border-obsidian-750 pb-1.5">
                    <span className="text-slate-400">B. Standard Deduction (16ia):</span>
                    <span className="text-slate-500">-{formatCurrency(taxComp.deduction_breakdown?.standard_deduction || 0)}</span>
                  </div>
                  <div className="flex justify-between border-b border-obsidian-750 pb-1.5">
                    <span className="text-slate-400">C. Other Sources (Interest):</span>
                    <span className="text-emerald-400 font-semibold">{formatCurrency(sumInterest(statements))}</span>
                  </div>
                  <div className="flex justify-between border-b border-obsidian-750 pb-1.5 font-bold text-slate-100">
                    <span>D. Gross Total Income:</span>
                    <span>{formatCurrency(taxComp.gross_income || 0)}</span>
                  </div>
                  <div className="flex justify-between border-b border-obsidian-750 pb-1.5">
                    <span className="text-slate-400">E. Chapter VI-A Deductions:</span>
                    <span className="text-violet-400 font-semibold">-{formatCurrency(taxComp.total_deductions - (taxComp.deduction_breakdown?.standard_deduction || 0))}</span>
                  </div>
                  <div className="flex justify-between border-b border-obsidian-750 pb-1.5 font-bold text-amber-500">
                    <span>F. Net Taxable Income:</span>
                    <span>{formatCurrency(taxComp.taxable_income || 0)}</span>
                  </div>
                </div>

                <div className="bg-obsidian-900/80 p-3 rounded-xl border border-obsidian-700 space-y-2 shadow-inner">
                  <div className="flex justify-between"><span className="text-slate-400 font-bold">Total Tax Liability:</span> <span className="font-bold text-rose-400">{formatCurrency(taxComp.total_tax_liability || 0)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Less: Reconciled TDS Credit:</span> <span className="text-slate-300">{formatCurrency(taxComp.tds_already_paid || 0)}</span></div>
                  {taxComp.net_tax_payable > 0 ? (
                    <div className="flex justify-between pt-2 border-t border-obsidian-700 font-bold text-rose-500 text-xs"><span className="font-bold">Net Tax Due:</span> <span>{formatCurrency(taxComp.net_tax_payable)}</span></div>
                  ) : (
                    <div className="flex justify-between pt-2 border-t border-obsidian-700 font-bold text-emerald-400 text-xs"><span className="font-bold">Refund Due:</span> <span>{formatCurrency(Math.max(0, taxComp.tds_already_paid - taxComp.total_tax_liability))}</span></div>
                  )}
                </div>
              </div>
            </div>

            {/* Document Generation Action Cards */}
            <div className="card p-5 space-y-4 border border-obsidian-600 bg-obsidian-900">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Generate & Download Documents</h4>
              
              <div className="grid grid-cols-1 gap-3">
                {/* 1. ITR Portal JSON */}
                <div className="flex items-center justify-between p-3.5 rounded-xl bg-obsidian-800 border border-obsidian-700 hover:border-emerald-500/35 transition-colors">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      ITR-1 Portal E-Filing File (JSON)
                      <span className="text-[9px] font-mono text-emerald-450 bg-emerald-500/10 px-2 py-0.5 rounded font-normal border border-emerald-500/20">Ready-to-File</span>
                    </span>
                    <p className="text-slate-500 text-[10px]">Official JSON schema to upload directly to incometax.gov.in portal</p>
                  </div>
                  <button onClick={() => downloadITRDoc('json')} disabled={generatingDoc !== null}
                    className="p-2.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 hover:text-emerald-350 border border-emerald-500/20 transition-colors disabled:opacity-50">
                    <Download size={14} />
                  </button>
                </div>

                {/* 2. Official Return PDF */}
                <div className="flex items-center justify-between p-3.5 rounded-xl bg-obsidian-800 border border-obsidian-700 hover:border-rose-500/35 transition-colors">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-200">Official ITR-1 Return Form (PDF)</span>
                    <p className="text-slate-500 text-[10px]">Government-style structured Form ITR-1 Sahaj Return Acknowledgement</p>
                  </div>
                  <button onClick={() => downloadITRDoc('pdf')} disabled={generatingDoc !== null}
                    className="p-2.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-350 border border-rose-500/20 transition-colors disabled:opacity-50">
                    <Download size={14} />
                  </button>
                </div>

                {/* 3. Form 16 Summary PDF */}
                <div className="flex items-center justify-between p-3.5 rounded-xl bg-obsidian-800 border border-obsidian-700 hover:border-violet-500/35 transition-colors">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-200">Form 16 Salary & Tax Sheet (PDF)</span>
                    <p className="text-slate-500 text-[10px]">Tax Computation Certificate under Section 203 of the Income Tax Act</p>
                  </div>
                  <button onClick={() => downloadITRDoc('form16')} disabled={generatingDoc !== null}
                    className="p-2.5 rounded-lg bg-violet-500/10 hover:bg-violet-500/20 text-violet-400 hover:text-violet-350 border border-violet-500/20 transition-colors disabled:opacity-50">
                    <Download size={14} />
                  </button>
                </div>

                {/* 4. Form 26AS PDF */}
                <div className="flex items-center justify-between p-3.5 rounded-xl bg-obsidian-800 border border-obsidian-700 hover:border-amber-500/35 transition-colors">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-200">Form 26AS Tax Credit Statement (PDF)</span>
                    <p className="text-slate-500 text-[10px]">Reconciled record of TDS credited against taxpayer PAN u/s 203AA</p>
                  </div>
                  <button onClick={() => downloadITRDoc('form26as')} disabled={generatingDoc !== null}
                    className="p-2.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 hover:text-amber-350 border border-amber-500/20 transition-colors disabled:opacity-50">
                    <Download size={14} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── CHAT TAB ─────────────────────────────────────────────────────── */}
      {activeTab === 'chat' && (
        <AICAChat taxContext={taxComp} financialContext={overview?.financial_summary} />
      )}
    </div>
  )
}
