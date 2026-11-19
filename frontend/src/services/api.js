/**
 * Opportunity Intelligence — Global Edition
 * Centralized Frontend API Client (src/services/api.js)
 */

const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMessage =
        (Array.isArray(data.detail)
          ? data.detail.map((d) => d.msg).join(', ')
          : data.detail) ||
        data.message ||
        `Request failed with status ${response.status}`;
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      throw new Error(
        'Unable to connect to the FastAPI backend server. Please verify uvicorn is running on http://127.0.0.1:8000.'
      );
    }
    throw error;
  }
}

export async function checkHealth() {
  return request('/health');
}

export async function getCategories() {
  return request('/categories');
}

export async function getCountries(searchQuery = '') {
  const q = searchQuery ? `?q=${encodeURIComponent(searchQuery)}` : '';
  return request(`/countries${q}`);
}

export async function getCountrySubdivisions(countryNameOrIso) {
  return request(`/locations?country=${encodeURIComponent(countryNameOrIso)}`);
}

export async function getCurrencies(code = '') {
  const q = code ? `?code=${encodeURIComponent(code)}` : '';
  return request(`/currencies${q}`);
}

export async function convertCurrency({ amount, fromCurrency, toCurrency }) {
  const params = new URLSearchParams({
    amount: String(amount),
    from_currency: fromCurrency,
    to_currency: toCurrency,
  });
  return request(`/currency/convert?${params.toString()}`);
}

export async function getDashboardData(email = '') {
  const q = email ? `?email=${encodeURIComponent(email)}` : '';
  return request(`/dashboard${q}`);
}

export async function discoverOpportunities(payload) {
  return request('/discover', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getSearchHistory(emailOrOptions = '') {
  if (typeof emailOrOptions === 'string') {
    const q = emailOrOptions ? `?email=${encodeURIComponent(emailOrOptions)}` : '';
    return request(`/history${q}`);
  }
  const opts = emailOrOptions || {};
  const params = new URLSearchParams();
  if (opts.email) params.set('email', opts.email);
  if (opts.q) params.set('q', opts.q);
  if (opts.country && opts.country !== 'all') params.set('country', opts.country);
  if (opts.state && opts.state !== 'all') params.set('state', opts.state);
  if (opts.city && opts.city !== 'all') params.set('city', opts.city);
  if (opts.category && opts.category !== 'all') params.set('category', opts.category);
  if (opts.dateFrom) params.set('date_from', opts.dateFrom);
  if (opts.dateTo) params.set('date_to', opts.dateTo);
  if (opts.limit) params.set('limit', String(opts.limit));
  if (opts.offset !== undefined && opts.offset !== null) params.set('offset', String(opts.offset));
  if (opts.includeMeta) params.set('include_meta', 'true');
  const qs = params.toString();
  return request(`/history${qs ? `?${qs}` : ''}`);
}

export async function getHistoryRecordById(historyId, email = '') {
  const q = email ? `?email=${encodeURIComponent(email)}` : '';
  return request(`/history/${historyId}${q}`);
}

export async function deleteSearchHistory(historyId, email = '') {
  const q = email ? `?email=${encodeURIComponent(email)}` : '';
  return request(`/history/${historyId}${q}`, {
    method: 'DELETE',
  });
}

export async function saveOpportunityReport(userEmail, opportunity, notes = '') {
  return request('/reports/save', {
    method: 'POST',
    body: JSON.stringify({
      user_email: userEmail || 'guest@opportunity.ai',
      opportunity,
      notes,
    }),
  });
}

export async function getSavedReports(email = '') {
  const q = email ? `?email=${encodeURIComponent(email)}` : '';
  return request(`/reports/saved${q}`);
}

export async function deleteSavedReport(reportId, email = '') {
  const q = email ? `?email=${encodeURIComponent(email)}` : '';
  return request(`/reports/saved/${reportId}${q}`, {
    method: 'DELETE',
  });
}

export async function downloadOpportunityPdf(opportunity) {
  const response = await fetch(`${API_BASE}/reports/export-pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(opportunity),
  });
  if (!response.ok) {
    throw new Error('Failed to generate PDF report');
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  const safeTitle = (opportunity.title || 'Opportunity_Report')
    .replace(/[^a-zA-Z0-9]/g, '_')
    .slice(0, 35);
  a.href = url;
  a.download = `Opportunity_Report_${safeTitle}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function queryReportAssistant(question, opportunity) {
  return request('/assistant/query', {
    method: 'POST',
    body: JSON.stringify({ question, opportunity }),
  });
}

export async function getPromptCacheStats() {
  return request('/cache/stats');
}

export async function clearPromptCache(promptType = '') {
  const q = promptType ? `?prompt_type=${encodeURIComponent(promptType)}` : '';
  return request(`/cache/clear${q}`, {
    method: 'POST',
  });
}

export async function loginWithPassword(email, password, mode = 'auto') {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password, mode }),
  });
}

export async function startLogin(email) {
  return request('/auth/start', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export async function verifyLogin(email, code) {
  return request('/auth/verify', {
    method: 'POST',
    body: JSON.stringify({ email, code }),
  });
}
