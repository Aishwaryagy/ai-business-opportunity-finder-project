import React from 'react';

export default function ResultCard({ opportunity, onViewDetails }) {
  const {
    title,
    summary,
    targetCustomers,
    score
  } = opportunity;

  // Determine badge styling based on score
  const isHigh = score >= 85;

  return (
    <div className="opportunity-card">
      <div>
        <div className="card-top">
          <h3 className="opp-title">{title}</h3>
          <div className={`score-badge-circle ${isHigh ? 'high' : 'mid'}`} title="Opportunity Score">
            <span className="score-num">{score}</span>
            <span className="score-lbl">Score</span>
          </div>
        </div>

        <p className="opp-summary">{summary}</p>

        <div className="inferred-tag-box">
          <div className="inferred-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            Inferred Target Customers:
          </div>
          <div className="inferred-val">{targetCustomers}</div>
        </div>
      </div>

      <button
        type="button"
        className="btn-view-details"
        onClick={() => onViewDetails(opportunity)}
      >
        <span>View Details</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="5" y1="12" x2="19" y2="12"/>
          <polyline points="12 5 19 12 12 19"/>
        </svg>
      </button>
    </div>
  );
}
