import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ShieldCheck, ShieldAlert, Briefcase, FileText, CalendarCheck } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { dashboardApi } from '../services/api'

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-5">
      <div className="flex items-center gap-3">
        <div className="bg-blue-50 text-blue-600 rounded-lg p-2">
          <Icon size={20} />
        </div>
        <div>
          <p className="text-2xl font-semibold text-slate-900">{value}</p>
          <p className="text-sm text-slate-500">{label}</p>
        </div>
      </div>
      <p className="text-xs text-slate-400 mt-3">Coming in a later phase</p>
    </div>
  )
}

export default function Dashboard() {
  const { user, logout } = useAuth()
  const [summary, setSummary] = useState(null)

  useEffect(() => {
    dashboardApi.summary().then(setSummary).catch(() => {})
  }, [])

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">
              Welcome{user ? `, ${user.name}` : ''}
            </h1>
            <p className="text-sm text-slate-500">AI Job Application Agent</p>
          </div>
          <button onClick={logout} className="text-sm text-slate-500 hover:text-slate-900">
            Log out
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex flex-wrap gap-3 mb-8">
          <span
            className={`inline-flex items-center gap-1.5 text-sm rounded-full px-3 py-1 ${
              user?.is_email_verified ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'
            }`}
          >
            <ShieldCheck size={14} />
            {user?.is_email_verified ? 'Email verified' : 'Email not verified'}
          </span>

          {user?.mfa_enabled ? (
            <span className="inline-flex items-center gap-1.5 text-sm rounded-full px-3 py-1 bg-green-50 text-green-700">
              <ShieldCheck size={14} /> Two-factor authentication enabled
            </span>
          ) : (
            <Link
              to="/mfa-setup"
              className="inline-flex items-center gap-1.5 text-sm rounded-full px-3 py-1 bg-amber-50 text-amber-700 hover:bg-amber-100"
            >
              <ShieldAlert size={14} /> Set up two-factor authentication
            </Link>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <StatCard icon={Briefcase} label="Jobs matched" value={summary?.stats.jobs_matched ?? '—'} />
          <StatCard icon={FileText} label="Applications" value={summary?.stats.applications_total ?? '—'} />
          <StatCard icon={CalendarCheck} label="Interviews" value={summary?.stats.interviews ?? '—'} />
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Next steps</h2>
          <ul className="space-y-2">
            {(summary?.next_steps ?? []).map((step) => (
              <li key={step} className="text-sm text-slate-600 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                {step}
              </li>
            ))}
          </ul>
        </div>
      </main>
    </div>
  )
}
