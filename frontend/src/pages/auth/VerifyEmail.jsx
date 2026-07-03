import { useEffect, useState } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { authApi, getErrorMessage } from '../../services/api'

export default function VerifyEmail() {
  const { resendVerification } = useAuth()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const emailFromState = location.state?.email || ''

  const [status, setStatus] = useState(token ? 'verifying' : 'pending')
  const [error, setError] = useState('')
  const [resendMessage, setResendMessage] = useState('')
  const [email, setEmail] = useState(emailFromState)
  const [devVerifyUrl, setDevVerifyUrl] = useState(location.state?.devVerifyUrl || '')

  useEffect(() => {
    if (!token) return
    authApi
      .verifyEmail(token)
      .then(() => setStatus('verified'))
      .catch((err) => {
        setStatus('error')
        setError(getErrorMessage(err, 'Invalid or expired verification link.'))
      })
  }, [token])

  async function handleResend(e) {
    e.preventDefault()
    setResendMessage('')
    try {
      const result = await resendVerification(email)
      setResendMessage('If an account exists and is unverified, a new email has been sent.')
      setDevVerifyUrl(result.dev_verify_url || '')
    } catch (err) {
      setResendMessage(getErrorMessage(err, 'Something went wrong. Please try again.'))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm bg-white rounded-xl shadow-sm p-8 text-center">
        {status === 'verifying' && <p className="text-slate-600">Verifying your email...</p>}

        {status === 'verified' && (
          <>
            <h1 className="text-xl font-semibold text-slate-900 mb-2">Email verified</h1>
            <p className="text-slate-500 text-sm mb-6">Your account is ready. You can now log in.</p>
            <Link to="/login" className="inline-block bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium">
              Go to login
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <h1 className="text-xl font-semibold text-slate-900 mb-2">Verification failed</h1>
            <p className="text-red-600 text-sm mb-6">{error}</p>
          </>
        )}

        {status === 'pending' && (
          <>
            <h1 className="text-xl font-semibold text-slate-900 mb-2">Check your email</h1>
            <p className="text-slate-500 text-sm mb-6">
              We've sent a verification link to {emailFromState || 'your inbox'}. Click it to activate your account.
            </p>
          </>
        )}

        {devVerifyUrl && (
          <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4 break-all">
            Dev mode (SMTP not configured):{' '}
            <a href={devVerifyUrl} className="underline font-medium">
              click here to verify
            </a>
          </p>
        )}

        {(status === 'pending' || status === 'error') && (
          <form onSubmit={handleResend} className="space-y-3 mt-2">
            <input
              type="email"
              required
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="w-full bg-slate-900 text-white rounded-lg py-2 text-sm font-medium hover:bg-slate-800"
            >
              Resend verification email
            </button>
            {resendMessage && <p className="text-xs text-slate-500">{resendMessage}</p>}
          </form>
        )}

        <p className="text-sm text-slate-500 mt-6">
          <Link to="/login" className="text-blue-600 font-medium">
            Back to login
          </Link>
        </p>
      </div>
    </div>
  )
}
