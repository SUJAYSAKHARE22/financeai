import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, ArrowLeftRight, PieChart, Target, Bot, ChevronLeft, ChevronRight, TrendingUp, Sparkles } from 'lucide-react'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/transactions', icon: ArrowLeftRight, label: 'Transactions' },
  { to: '/budgets', icon: PieChart, label: 'Budgets' },
  { to: '/goals', icon: Target, label: 'Goals' },
  { to: '/ai-advisor', icon: Bot, label: 'AI Advisor', highlight: true },
]

export default function Sidebar({ open, setOpen }) {
  return (
    <aside className={`fixed left-0 top-0 h-full z-50 flex flex-col transition-all duration-300 border-r border-obsidian-600 glass ${open ? 'w-64' : 'w-16'}`}>
      <div className="flex items-center gap-3 px-4 py-5 border-b border-obsidian-600 min-h-[72px]">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-500 to-violet-500 flex items-center justify-center flex-shrink-0 shadow-lg">
          <TrendingUp size={16} className="text-white" />
        </div>
        {open && (
          <div className="overflow-hidden">
            <div className="text-base font-bold text-slate-100 whitespace-nowrap">FinanceAI</div>
            <div className="text-xs text-emerald-400 font-medium whitespace-nowrap">Smart Money Manager</div>
          </div>
        )}
      </div>

      <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label, highlight }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `nav-item ${isActive ? 'nav-item-active' : ''}`}>
            {({ isActive }) => (
              <>
                <div className={`relative flex-shrink-0 ${highlight && !isActive ? 'text-violet-400' : ''}`}>
                  <Icon size={18} />
                  {highlight && <span className="absolute -top-1 -right-1 w-2 h-2 bg-violet-400 rounded-full animate-pulse" />}
                </div>
                {open && (
                  <span className="whitespace-nowrap">
                    {label}
                    {highlight && <Sparkles size={12} className="inline ml-1 text-violet-400" />}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="px-2 py-4 border-t border-obsidian-600">
        <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-slate-500 hover:text-slate-300 hover:bg-obsidian-700 transition-all text-xs">
          {open ? <><ChevronLeft size={16} /><span>Collapse</span></> : <ChevronRight size={16} />}
        </button>
      </div>
    </aside>
  )
}
