import React from 'react';

export default function ScoreCard({ score, breakdown }) {
  if (!breakdown) return null;

  const factors = [
    { label: 'Customer Need', value: breakdown.customerNeed, desc: 'Pain intensity & urgency' },
    { label: 'Market Demand', value: breakdown.marketDemand, desc: 'Target volume & adoption willingness' },
    { label: 'Competition (Gap)', value: breakdown.competition, desc: 'Room for new entrance' },
    { label: 'Growth Potential', value: breakdown.growthPotential, desc: 'Future scalability headroom' },
    { label: 'Feasibility', value: breakdown.feasibility, desc: 'Capital & operational viability' },
  ];

  const getScoreColor = (val) => {
    if (val >= 85) return '#10b981'; // Green
    if (val >= 70) return '#3b82f6'; // Blue
    return '#f59e0b'; // Amber
  };

  return (
    <div className="score-breakdown-container">
      <div className="breakdown-header">
        <div>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '2px' }}>
            Opportunity Score Breakdown
          </h4>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Multidimensional viability assessment out of 100
          </span>
        </div>
        <div className="overall-score-pill" style={{ backgroundColor: getScoreColor(score) }}>
          <span>Overall Score: {score}/100</span>
        </div>
      </div>

      <div className="breakdown-grid">
        {factors.map((item) => (
          <div key={item.label} className="factor-card">
            <div className="factor-top">
              <span>{item.label}</span>
              <strong style={{ color: getScoreColor(item.value) }}>{item.value}</strong>
            </div>
            <div className="factor-bar-track">
              <div
                className="factor-bar-fill"
                style={{
                  width: `${item.value}%`,
                  backgroundColor: getScoreColor(item.value)
                }}
              />
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              {item.desc}
            </div>
          </div>
        ))}
      </div>

      <p className="score-disclaimer">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <span>
          Opportunity Score evaluates market dynamics and comparative viability. It does not represent an exact prediction or guarantee of business success.
        </span>
      </p>
    </div>
  );
}
