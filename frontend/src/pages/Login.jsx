import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../components/AuthContext'
import { authAPI } from '../utils/api'
import { toast } from 'react-hot-toast'
import { Lock, User, ArrowLeft, TrendingUp } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username || !password) {
      toast.error('Please fill in all fields')
      return
    }

    setLoading(true)
    try {
      const resp = await authAPI.login(username, password)
      login(resp.data.token, resp.data.username)
      toast.success(`Welcome back, ${resp.data.username}!`)
      navigate('/dashboard')
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Invalid credentials'
      toast.error(errMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-obsidian-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full bg-violet-600/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full bg-emerald-500/5 blur-[120px] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-300 transition-colors mb-6 ml-4 sm:ml-0">
          <ArrowLeft size={16} /> Back to Home
        </Link>
        <div className="flex justify-center">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-violet-500 flex items-center justify-center shadow-lg shadow-emerald-500/10">
            <TrendingUp size={20} className="text-white" />
          </div>
        </div>
        <h2 className="mt-4 text-center text-3xl font-extrabold text-slate-100 tracking-tight">
          Welcome back
        </h2>
        <p className="mt-2 text-center text-sm text-slate-500">
          Manage your personal finances securely
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4 sm:px-0">
        <div className="bg-obsidian-800/80 backdrop-blur-md py-8 px-6 border border-obsidian-600 rounded-3xl shadow-xl sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="username" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Username
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <User size={16} />
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  className="input-field pl-10"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock size={16} />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-field pl-10"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center btn-primary py-3 hover:scale-[1.01] transition-transform active:scale-[0.99] disabled:opacity-50 disabled:pointer-events-none"
              >
                {loading ? 'Logging in...' : 'Log In'}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-slate-500">
              Don't have an account?{' '}
              <Link to="/signup" className="text-emerald-400 hover:text-emerald-300 font-semibold transition-colors">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
