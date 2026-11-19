import React, { useState } from 'react';
import {
  Briefcase,
  Mail,
  Lock,
  ShieldCheck,
  ArrowRight,
  Eye,
  EyeOff,
  X,
  KeyRound,
} from 'lucide-react';
import { loginWithPassword } from '../services/api';

export default function LoginPage({ onLoginSuccess, onCancel }) {
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    const cleanEmail = email.trim();
    if (!cleanEmail || !cleanEmail.includes('@')) {
      setErrorMsg('Please enter a valid email address.');
      return;
    }

    if (!password || password.length < 6) {
      setErrorMsg('Password must be at least 6 characters long.');
      return;
    }

    if (authMode === 'register' && password !== confirmPassword) {
      setErrorMsg('Passwords do not match. Please verify both fields.');
      return;
    }

    setIsLoading(true);
    try {
      const modeParam = authMode === 'register' ? 'register' : 'auto';
      const res = await loginWithPassword(cleanEmail, password, modeParam);
      if (res.success && res.user) {
        onLoginSuccess(res.user);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Authentication failed. Please check your password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="glass-panel w-full max-w-md p-6 sm:p-8 relative">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="absolute right-4 top-4 p-1.5 rounded-lg bg-slate-900 text-slate-400 hover:text-white border border-slate-800 cursor-pointer transition"
          >
            <X className="w-4 h-4" />
          </button>
        )}

        <div className="text-center mb-6">
          <div className="w-11 h-11 rounded-xl bg-blue-600 flex items-center justify-center mx-auto mb-3 shadow-sm">
            <Briefcase className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Workspace Authentication
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Secured with <strong className="text-blue-400">PBKDF2-HMAC-SHA256</strong> Salted Password Hashing
          </p>
        </div>

        {/* Sign In / Create Account Mode Switcher */}
        <div className="grid grid-cols-2 gap-1.5 p-1 rounded-lg bg-slate-900 border border-slate-800 mb-5">
          <button
            type="button"
            onClick={() => {
              setAuthMode('login');
              setErrorMsg('');
            }}
            className={`py-2 rounded-md text-xs font-semibold transition cursor-pointer ${
              authMode === 'login'
                ? 'btn-primary-text bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setAuthMode('register');
              setErrorMsg('');
            }}
            className={`py-2 rounded-md text-xs font-semibold transition cursor-pointer ${
              authMode === 'register'
                ? 'btn-primary-text bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Create Account
          </button>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs mb-4">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                placeholder="founder@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-10 pl-10 pr-4 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Password (Min. 6 Characters)
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={6}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-10 pl-10 pr-10 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-slate-400 hover:text-white cursor-pointer"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {authMode === 'register' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Confirm Password
              </label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  minLength={6}
                  placeholder="Re-enter your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full h-10 pl-10 pr-4 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary-text w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm flex items-center justify-center gap-2 cursor-pointer shadow-sm transition"
          >
            <ShieldCheck className="w-4 h-4 text-white" />
            <span className="text-white">
              {isLoading
                ? 'Verifying Credentials...'
                : authMode === 'register'
                ? 'Create Account'
                : 'Sign In'}
            </span>
            <ArrowRight className="w-4 h-4 text-white" />
          </button>

          <div className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800 text-[11px] text-slate-400 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              Credentials are hashed via{' '}
              <code className="text-blue-400">PBKDF2-HMAC-SHA256</code> (260,000 iterations +
              128-bit salt).
            </span>
          </div>
        </form>
      </div>
    </div>
  );
}
