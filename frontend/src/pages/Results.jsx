import React, { useState } from 'react';
import ResultCard from '../components/ResultCard';
import ScoreCard from '../components/ScoreCard';

export default function Results({
  analysisData,
  onNewSearch
}) {
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);

  if (!analysisData || !analysisData.opportunities) {
    return (
      <div className="empty-state">
        <h3>No analysis results found</h3>
        <p>Please perform a search to discover business opportunities.</p>
        <button
          className="btn-primary"
          style={{ maxWidth: '240px', margin: '20px auto 0 auto' }}
          onClick={onNewSearch}
        >
          Start New Search
        </button>
      </div>
    );
  }

  const {
    domain,
    city,
    area,
    userQuery,
    opportunities,
    marketContextSummary
  } = analysisData;

  return (
    <div>
      {/* Results Header */}
      <div className="results-header">
        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', marginBottom: '6px' }}>
            Potential Business Opportunities
          </h2>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <span className="results-meta-pill">
              <strong>Domain:</strong> {domain}
            </span>
            <span className="results-meta-pill">
              <strong>Location:</strong> {city} · {area}
            </span>
            {userQuery && (
              <span className="results-meta-pill" style={{ fontStyle: 'italic', maxWidth: '380px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                "{userQuery}"
              </span>
            )}
          </div>
        </div>

        <div>
          <button
            type="button"
            className="btn-nav"
            onClick={onNewSearch}
            style={{ fontWeight: 700 }}
          >
            ← Modify Search
          </button>
        </div>
      </div>

      {/* Market context summary if available */}
      {marketContextSummary && (
        <div style={{ backgroundColor: '#ffffff', border: '1px solid var(--border)', borderRadius: '12px', padding: '14px 18px', marginBottom: '24px', fontSize: '0.875rem', color: 'var(--text-secondary)', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
          <span style={{ fontSize: '1.1rem' }}>📍</span>
          <div>
            <strong>Hyperlocal Market Context:</strong> {marketContextSummary}
          </div>
        </div>
      )}

      {/* Opportunities Grid */}
      <div className="cards-grid">
        {opportunities.map((opp) => (
          <ResultCard
            key={opp.id}
            opportunity={opp}
            onViewDetails={(selected) => setSelectedOpportunity(selected)}
          />
        ))}
      </div>

      {/* Detailed Opportunity Modal */}
      {selectedOpportunity && (
        <div className="modal-overlay" onClick={() => setSelectedOpportunity(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="modal-header">
              <div>
                <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--primary)', fontWeight: 800 }}>
                  Detailed Opportunity Analysis
                </span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '4px' }}>
                  {selectedOpportunity.title}
                </h2>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setSelectedOpportunity(null)}
                title="Close modal"
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div className="modal-body">
              {/* Score Breakdown Section */}
              <ScoreCard
                score={selectedOpportunity.score}
                breakdown={selectedOpportunity.scoreBreakdown}
              />

              {/* 1. Overview */}
              <div className="detail-section">
                <div className="detail-section-title">
                  <span>💡 Overview</span>
                </div>
                <div className="detail-section-body">
                  {selectedOpportunity.summary}
                </div>
              </div>

              {/* 2. Target Customers */}
              <div className="detail-section">
                <div className="detail-section-title">
                  <span>🎯 Target Customers</span>
                </div>
                <div className="detail-section-body">
                  {selectedOpportunity.targetCustomers}
                </div>
              </div>

              {/* 3. Customer Problem */}
              <div className="detail-section">
                <div className="detail-section-title">
                  <span>⚠️ Customer Problem</span>
                </div>
                <div className="detail-section-body">
                  {selectedOpportunity.customerProblem}
                </div>
              </div>

              {/* 4. Market Gap */}
              <div className="detail-section">
                <div className="detail-section-title">
                  <span>🚀 Market Gap</span>
                </div>
                <div className="detail-section-body">
                  {selectedOpportunity.marketGap}
                </div>
              </div>

              {/* 5. Competitor / Market Context */}
              <div className="detail-section">
                <div className="detail-section-title">
                  <span>🏢 Competitor & Market Context</span>
                </div>
                <div className="detail-section-body" style={{ borderLeft: '3px solid #6366f1' }}>
                  {selectedOpportunity.competitorContext}
                </div>
              </div>

              {/* 6. Suggested Business Model */}
              <div className="detail-section">
                <div className="detail-section-title">
                  <span>💰 Suggested Business Model</span>
                </div>
                <div className="detail-section-body" style={{ background: '#f0fdf4', borderColor: '#bbf7d0' }}>
                  <strong style={{ color: '#166534' }}>Monetization Strategy: </strong>
                  {selectedOpportunity.businessModel}
                </div>
              </div>

              {/* 7. Why This Opportunity? */}
              <div className="detail-section">
                <div className="detail-section-title">
                  <span>⭐ Why This Opportunity?</span>
                </div>
                <div className="detail-section-body" style={{ background: '#fdf4ff', borderColor: '#f5d0fe' }}>
                  {selectedOpportunity.whyThisOpportunity}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
