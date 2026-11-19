import React from 'react';

export default function HistoryCard({ item, onViewOpportunities }) {
  const {
    domain,
    city,
    area,
    user_query,
    opportunities = [],
    created_at
  } = item;

  // Format date nicely
  const formatDate = (dateString) => {
    try {
      const d = new Date(dateString);
      if (isNaN(d.getTime())) return dateString;
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="history-item-card">
      <div className="history-meta">
        <div className="history-tags">
          <span className="badge-domain">{domain}</span>
          <span className="badge-location">{city} · {area}</span>
          <span className="history-date">📅 {formatDate(created_at)}</span>
        </div>

        {user_query && (
          <p className="history-query-text">
            "{user_query}"
          </p>
        )}

        <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
          {opportunities.length} opportunities generated
        </div>
      </div>

      <div>
        <button
          type="button"
          className="btn-nav btn-nav-active"
          onClick={() => onViewOpportunities(item)}
        >
          <span>View Opportunities</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>
    </div>
  );
}
