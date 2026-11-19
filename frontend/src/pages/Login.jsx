import React, { useState } from 'react';
import { startLogin, verifyLogin } from '../services/api';

export default function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [step, setStep] = useState('email'); // 'email' | 'otp'
  const [otpCode, setOtpCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [infoMsg, setInfoMsg] = useState('');
  const [isSmtpActive, setIsSmtpActive] = useState(false);
  const [devCodeHint, setDevCodeHint] = useState('');

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setInfoMsg('');

    if (!email || !email.includes('@')) {
      setErrorMsg('Please enter a valid email address.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await startLogin(email);
      setStep('otp');
      setIsSmtpActive(Boolean(res.is_smtp_sent));
      setInfoMsg(res.message);

      if (res.is_smtp_sent) {
        setDevCodeHint('');
        setOtpCode(''); // Keep blank so user types the code from their real email
      } else {
        // If SMTP is not yet configured, show the generated code for testing
        setDevCodeHint(res.dev_code || '123456');
        setOtpCode(res.dev_code || '123456');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to initiate login. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!otpCode || otpCode.trim().length !== 6) {
      setErrorMsg('Please enter the 6-digit verification code.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await verifyLogin(email, otpCode.trim());
      if (res.success && res.user) {
        onLoginSuccess(res.user);
      } else {
        setErrorMsg('Verification failed. Please check the code.');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Verification failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setErrorMsg('');
    setIsLoading(true);
    try {
      const res = await startLogin(email);
      setIsSmtpActive(Boolean(res.is_smtp_sent));
      setInfoMsg(res.message);
      if (res.dev_code) {
        setDevCodeHint(res.dev_code);
        setOtpCode(res.dev_code);
      }
    } catch (err) {
      setErrorMsg('Failed to resend code: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-card">
        {/* Logo and Title */}
        <div className="login-header">
          <div
            className="brand-logo-icon"
            style={{ width: '48px', height: '48px', margin: '0 auto', fontSize: '1.25rem' }}
          >
            <span>AI</span>
          </div>
          <h1 className="login-title">AI Business Opportunity Finder</h1>
          <p className="login-subtitle">
            Discover vetted market gaps and hyper-local venture opportunities
          </p>
        </div>

        {/* Development Helper Banner (Only when SMTP is unconfigured) */}
        {!isSmtpActive && (
          <div className="dev-otp-banner">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <div>
              <strong>Email Verification Ready:</strong> Enter any real email. {devCodeHint ? <>Use code <code>{devCodeHint}</code> (or configure SMTP in <code>backend/.env</code> for live inbox delivery).</> : <>Configure SMTP in <code>backend/.env</code> to receive live inbox emails.</>}
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="error-alert">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Info Alert */}
        {infoMsg && (
          <div style={{ backgroundColor: isSmtpActive ? '#ecfdf5' : '#eff6ff', border: isSmtpActive ? '1px solid #a7f3d0' : '1px solid #bfdbfe', color: isSmtpActive ? '#065f46' : '#1e40af', padding: '12px 14px', borderRadius: '8px', fontSize: '0.85rem', marginBottom: '18px', display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
            <span>{isSmtpActive ? '✉️' : 'ℹ️'}</span>
            <span>{infoMsg}</span>
          </div>
        )}

        {step === 'email' ? (
          /* Step 1: Email Form */
          <form onSubmit={handleEmailSubmit}>
            <div className="form-group" style={{ marginBottom: '20px' }}>
              <label className="form-label" htmlFor="login-email">
                Your Email Address
              </label>
              <input
                id="login-email"
                type="email"
                className="form-control"
                placeholder="you@domain.com or test@gmail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                autoFocus
                required
              />
              <span className="form-helper">
                Enter your real email address. Your search history will be saved to SQLite under this account.
              </span>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Sending Verification Code...' : 'Send Verification Code →'}
            </button>
          </form>
        ) : (
          /* Step 2: OTP Verification Form */
          <form onSubmit={handleOtpSubmit}>
            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label" htmlFor="login-otp">
                6-Digit Verification Code
              </label>
              <input
                id="login-otp"
                type="text"
                className="form-control"
                placeholder="123456"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                maxLength={6}
                disabled={isLoading}
                autoFocus
                style={{ textAlign: 'center', letterSpacing: '0.25em', fontSize: '1.35rem', fontWeight: 'bold' }}
                required
              />
              <span className="form-helper" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                <span>Sent to: <strong>{email}</strong></span>
                <button
                  type="button"
                  onClick={handleResend}
                  style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer', fontSize: '0.8rem', padding: 0 }}
                  disabled={isLoading}
                >
                  Resend code
                </button>
              </span>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
              style={{ marginBottom: '12px' }}
            >
              {isLoading ? 'Verifying...' : 'Verify Code & Open Dashboard →'}
            </button>

            <button
              type="button"
              className="btn-nav"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => {
                setStep('email');
                setErrorMsg('');
                setInfoMsg('');
              }}
              disabled={isLoading}
            >
              ← Use a different email
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
