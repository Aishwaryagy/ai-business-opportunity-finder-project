import React from 'react';

export default function Header({ userEmail, currentPage, onNavigate, onLogout }) {
  return (
    <header className="header-bar">
      <div className="header-inner">
        {/* Brand */}
        <div className="brand-wrapper" onClick={() => onNavigate('home')}>
          <div className="brand-logo-icon">
            <span>AI</span>
          </div>
          <div className="brand-titles">
            <span className="brand-title">AI Business Opportunity Finder</span>
            <span className="brand-subtitle">Hyperlocal Market & Venture Intelligence</span>
          </div>
        </div>

        {/* Navigation & User actions */}
        <div className="nav-actions">
          <button
            className={`btn-nav ${currentPage === 'home' ? 'btn-nav-active' : ''}`}
            onClick={() => onNavigate('home')}
            type="button"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            Dashboard
          </button>

          <button
            className={`btn-nav ${currentPage === 'history' ? 'btn-nav-active' : ''}`}
            onClick={() => onNavigate('history')}
            type="button"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            Search History
          </button>

          {userEmail && (
            <div className="user-badge" title="Logged in user">
              <div className="user-avatar-circle">
                {userEmail.charAt(0).toUpperCase()}
              </div>
              <span>{userEmail}</span>
            </div>
          )}

          <button
            className="btn-nav btn-logout"
            onClick={onLogout}
            type="button"
            title="Log out of current session"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
