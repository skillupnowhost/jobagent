import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { getErrorMessage } from '../../services/api'

export default function MFAChallenge() {
  const { mfaRequired, verifyMfa } = useAuth()
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [useBackupCode, setUseBackupCode] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!mfaRequired) {
    return <Navigate to="/login" replace />
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await verifyMfa(code)
      navigate('/')
    } catch (err) {
      setError(getErrorMessage(err, 'Invalid code. Please try again.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm bg-white rounded-xl shadow-sm p-8">
        <h1 className="text-2xl font-semibold text-slate-900 mb-1">Two-factor verification</h1>
        <p className="text-slate-500 text-sm mb-6">
          {useBackupCode
            ? 'Enter one of your backup codes.'
            : 'Enter the 6-digit code from your authenticator app.'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            required
            autoFocus
            inputMode={useBackupCode ? 'text' : 'numeric'}
            maxLength={useBackupCode ? 10 : 6}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder={useBackupCode ? 'Backup code' : '123456'}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-60"
          >
            {submitting ? 'Verifying...' : 'Verify'}
          </button>
        </form>

        <button
          type="button"
          onClick={() => {
            setUseBackupCode((v) => !v)
            setCode('')
            setError('')
          }}
          className="text-sm text-blue-600 font-medium mt-4"
        >
          {useBackupCode ? 'Use authenticator code instead' : 'Use a backup code instead'}
        </button>
      </div>
    </div>
  )
}
