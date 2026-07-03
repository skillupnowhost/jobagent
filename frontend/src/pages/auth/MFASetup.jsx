import { useEffect, useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { authApi, getErrorMessage } from '../../services/api'

export default function MFASetup() {
  const { refreshUser } = useAuth()
  const navigate = useNavigate()

  const [setupData, setSetupData] = useState(null)
  const [code, setCode] = useState('')
  const [backupCodes, setBackupCodes] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    authApi
      .mfaSetup()
      .then(setSetupData)
      .catch((err) => setError(getErrorMessage(err, 'Could not start MFA setup.')))
      .finally(() => setLoading(false))
  }, [])

  async function handleConfirm(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const result = await authApi.mfaConfirm(code)
      setBackupCodes(result.backup_codes)
      await refreshUser()
    } catch (err) {
      setError(getErrorMessage(err, 'Invalid code. Please try again.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-sm p-8">
        <h1 className="text-2xl font-semibold text-slate-900 mb-1">Set up two-factor authentication</h1>

        {loading && <p className="text-slate-500 text-sm mt-4">Loading...</p>}

        {!loading && backupCodes && (
          <div className="mt-4">
            <p className="text-green-700 text-sm mb-4">
              MFA is enabled. Save these backup codes somewhere safe — each can be used once if you lose access
              to your authenticator app.
            </p>
            <div className="grid grid-cols-2 gap-2 bg-slate-50 rounded-lg p-4 font-mono text-sm mb-6">
              {backupCodes.map((c) => (
                <span key={c}>{c}</span>
              ))}
            </div>
            <button
              onClick={() => navigate('/')}
              className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700"
            >
              Continue to dashboard
            </button>
          </div>
        )}

        {!loading && !backupCodes && setupData && (
          <>
            <p className="text-slate-500 text-sm mb-4">
              Scan this QR code with an authenticator app (e.g. Google Authenticator, Authy), then enter the
              6-digit code to confirm.
            </p>
            <div className="flex justify-center mb-4">
              <QRCodeSVG value={setupData.otpauth_url} size={180} />
            </div>
            <p className="text-xs text-slate-500 text-center mb-6 break-all">
              Can't scan? Enter this code manually: <span className="font-mono">{setupData.secret}</span>
            </p>

            <form onSubmit={handleConfirm} className="space-y-4">
              <input
                required
                autoFocus
                inputMode="numeric"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="123456"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-60"
              >
                {submitting ? 'Confirming...' : 'Confirm'}
              </button>
            </form>
          </>
        )}

        {!loading && !setupData && !backupCodes && (
          <p className="text-sm text-red-600 mt-4">{error}</p>
        )}
      </div>
    </div>
  )
}
