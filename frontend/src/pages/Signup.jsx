import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../utils/api'
import { toast } from 'react-hot-toast'
import { Lock, User, ArrowLeft, TrendingUp } from 'lucide-react'

export default function Signup() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (username.length < 3) {
      toast.error('Username must be at least 3 characters')
      return
    }
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters')
      return
    }
    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    setLoading(true)
    try {
      await authAPI.register(username, password)
      toast.success('Registration successful! Please log in.')
      navigate('/login')
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Registration failed'
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
          Create account
        </h2>
        <p className="mt-2 text-center text-sm text-slate-500">
          Start planning and tracking your finances privately
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
                  placeholder="At least 3 characters"
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
                  placeholder="At least 6 characters"
                  className="input-field pl-10"
                />
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Confirm Password
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock size={16} />
                </div>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
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
                {loading ? 'Creating account...' : 'Create Account'}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-slate-500">
              Already have an account?{' '}
              <Link to="/login" className="text-emerald-400 hover:text-emerald-300 font-semibold transition-colors">
                Log in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
