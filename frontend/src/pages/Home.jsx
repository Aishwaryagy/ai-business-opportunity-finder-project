import React from 'react';
import InputForm from '../components/InputForm';

export default function Home({
  domains,
  locations,
  onAnalyze,
  isLoading,
  error
}) {
  return (
    <div>
      {/* Hero Banner */}
      <div className="hero-banner">
        <div className="hero-tag">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
          Market Discovery Engine
        </div>
        <h1 className="hero-title">
          Find your next <span className="hero-title-highlight">business opportunity.</span>
        </h1>
        <p className="hero-subtitle">
          Explore potential business opportunities based on your domain, location and market needs.
        </p>
      </div>

      {/* Global Error Banner if any */}
      {error && (
        <div className="error-alert" style={{ maxWidth: '800px', margin: '0 auto 24px auto' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Main Form */}
      <div style={{ maxWidth: '960px', margin: '0 auto' }}>
        <InputForm
          domains={domains}
          locations={locations}
          onSubmit={onAnalyze}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
