import React, { useEffect, useState } from 'react';
import { getHistory } from '../services/api';
import HistoryCard from '../components/HistoryCard';

export default function History({ userEmail, onSelectHistoryItem, onNewSearch }) {
  const [historyItems, setHistoryItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    async function fetchUserHistory() {
      if (!userEmail) return;
      setIsLoading(true);
      setError('');
      try {
        const data = await getHistory(userEmail);
        if (isMounted) {
          setHistoryItems(data || []);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to load search history.');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    fetchUserHistory();

    return () => {
      isMounted = false;
    };
  }, [userEmail]);

  return (
    <div>
      <div className="results-header">
        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            Search History
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.925rem' }}>
            Previous market opportunity assessments saved to your SQLite database for <strong>{userEmail}</strong>
          </p>
        </div>

        <div>
          <button
            type="button"
            className="btn-primary"
            style={{ width: 'auto', padding: '10px 20px' }}
            onClick={onNewSearch}
          >
            + New Analysis
          </button>
        </div>
      </div>

      {error && (
        <div className="error-alert">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="loading-box">
          <div className="spinner" />
          <div className="loading-text">Loading search history...</div>
          <div className="loading-subtext">Fetching records from SQLite database</div>
        </div>
      ) : historyItems.length === 0 ? (
        <div className="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ margin: '0 auto 16px auto', display: 'block' }}>
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          <h3 style={{ fontSize: '1.25rem', color: 'var(--text-main)', marginBottom: '8px' }}>No searches recorded yet</h3>
          <p style={{ maxWidth: '420px', margin: '0 auto 20px auto' }}>
            Once you perform opportunity discovery searches, they will be archived here for persistent review.
          </p>
          <button
            type="button"
            className="btn-primary"
            style={{ width: 'auto', margin: '0 auto', display: 'inline-flex' }}
            onClick={onNewSearch}
          >
            Start Your First Discovery
          </button>
        </div>
      ) : (
        <div className="history-list">
          {historyItems.map((item) => (
            <HistoryCard
              key={item.id}
              item={item}
              onViewOpportunities={(selectedItem) => {
                onSelectHistoryItem({
                  domain: selectedItem.domain,
                  city: selectedItem.city,
                  area: selectedItem.area,
                  userQuery: selectedItem.user_query,
                  opportunities: selectedItem.opportunities,
                  marketContextSummary: `Archived search from ${new Date(selectedItem.created_at).toLocaleDateString()}`
                });
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
