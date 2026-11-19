import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Clock,
  Search,
  Filter,
  MapPin,
  Wallet,
  Trash2,
  ArrowUpRight,
  Compass,
  Calendar,
  Layers,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  X,
  SlidersHorizontal,
} from 'lucide-react';
import { getSearchHistory, deleteSearchHistory } from '../services/api';

const PAGE_SIZE = 8;

function formatDateTime(isoStr) {
  if (!isoStr) return '—';
  const cleaned = String(isoStr).replace('T', ' ').slice(0, 19);
  return cleaned;
}

export default function HistoryPage({
  userEmail,
  initialHistory = [],
  onSelectHistorySearch,
  onSelectOpportunity,
  onNavigateDiscover,
  onHistoryChanged,
}) {
  const [records, setRecords] = useState(initialHistory);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Search & Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('all');
  const [selectedState, setSelectedState] = useState('all');
  const [selectedCity, setSelectedCity] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Pagination / Load More state
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  // Expanded preview & delete confirmation modal states
  const [expandedId, setExpandedId] = useState(null);
  const [recordToDelete, setRecordToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchUserHistory = useCallback(async () => {
    if (!userEmail) {
      setRecords([]);
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const data = await getSearchHistory({
        email: userEmail,
        limit: 200,
        offset: 0,
      });
      setRecords(Array.isArray(data) ? data : data?.items || []);
    } catch (err) {
      setError(err.message || 'Unable to load search history.');
    } finally {
      setIsLoading(false);
    }
  }, [userEmail]);

  useEffect(() => {
    fetchUserHistory();
  }, [fetchUserHistory]);

  // Reset pagination count when filters change
  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [searchQuery, selectedCountry, selectedState, selectedCity, selectedCategory, dateFrom, dateTo]);

  // Dynamic filter dropdown options derived from the user's actual history records
  const filterOptions = useMemo(() => {
    const countries = new Set();
    const states = new Set();
    const cities = new Set();
    const categories = new Set();

    records.forEach((r) => {
      if (r.country) countries.add(r.country);
      if (r.state && (selectedCountry === 'all' || r.country === selectedCountry)) {
        states.add(r.state);
      }
      if (
        r.city &&
        (selectedCountry === 'all' || r.country === selectedCountry) &&
        (selectedState === 'all' || r.state === selectedState)
      ) {
        cities.add(r.city);
      }
      if (r.domain) categories.add(r.domain);
    });

    return {
      countries: Array.from(countries).sort(),
      states: Array.from(states).sort(),
      cities: Array.from(cities).sort(),
      categories: Array.from(categories).sort(),
    };
  }, [records, selectedCountry, selectedState]);

  // Filtered & reverse-chronological records (latest first)
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      if (selectedCountry !== 'all' && r.country !== selectedCountry) return false;
      if (selectedState !== 'all' && r.state !== selectedState) return false;
      if (selectedCity !== 'all' && r.city !== selectedCity) return false;
      if (selectedCategory !== 'all' && r.domain !== selectedCategory) return false;

      const recordDate = String(r.created_at || '').slice(0, 10);
      if (dateFrom && recordDate && recordDate < dateFrom) return false;
      if (dateTo && recordDate && recordDate > dateTo) return false;

      if (searchQuery.trim()) {
        const q = searchQuery.trim().toLowerCase();
        const oppTitles = (r.opportunities || []).map((o) => o.title).join(' ');
        const haystack = [
          r.domain,
          r.user_query,
          r.country,
          r.state,
          r.city,
          r.area,
          r.experience_level,
          r.risk_preference,
          r.data_status_label,
          oppTitles,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        if (!haystack.includes(q)) return false;
      }

      return true;
    });
  }, [
    records,
    selectedCountry,
    selectedState,
    selectedCity,
    selectedCategory,
    dateFrom,
    dateTo,
    searchQuery,
  ]);

  const displayedRecords = filteredRecords.slice(0, visibleCount);
  const hasMore = visibleCount < filteredRecords.length;

  const hasActiveFilters =
    Boolean(searchQuery.trim()) ||
    selectedCountry !== 'all' ||
    selectedState !== 'all' ||
    selectedCity !== 'all' ||
    selectedCategory !== 'all' ||
    Boolean(dateFrom) ||
    Boolean(dateTo);

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedCountry('all');
    setSelectedState('all');
    setSelectedCity('all');
    setSelectedCategory('all');
    setDateFrom('');
    setDateTo('');
  };

  const handleConfirmDelete = async () => {
    if (!recordToDelete || !userEmail) return;
    setIsDeleting(true);
    setError('');
    try {
      await deleteSearchHistory(recordToDelete.id, userEmail);
      setRecords((prev) => prev.filter((item) => item.id !== recordToDelete.id));
      setRecordToDelete(null);
      if (onHistoryChanged) {
        await onHistoryChanged();
      }
    } catch (err) {
      setError(err.message || 'Failed to delete search history record.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header & Summary Banner */}
      <div className="glass-panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-sm">
                <Clock className="w-5 h-5 text-white" strokeWidth={2.2} />
              </div>
              <div>
                <h1 className="text-xl font-extrabold text-white tracking-tight">
                  Search History
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  View, filter, reopen, or manage your personal opportunity discovery searches ({records.length} stored for{' '}
                  <strong className="text-slate-200">{userEmail}</strong>)
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={fetchUserHistory}
              disabled={isLoading}
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-200 border border-slate-800 flex items-center gap-1.5 cursor-pointer transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-blue-400 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>

            <button
              type="button"
              onClick={onNavigateDiscover}
              className="btn-primary-text px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs flex items-center gap-1.5 cursor-pointer transition shadow-sm"
            >
              <Compass className="w-4 h-4 text-white" />
              <span className="text-white">New Opportunity Search</span>
            </button>
          </div>
        </div>
      </div>

      {/* Search & Multi-Filter Control Panel */}
      <div className="glass-panel p-5 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          {/* Keyword Search Bar */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-blue-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search history by keyword, business category, city, area, or opportunity title..."
              className="w-full pl-10 pr-9 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs sm:text-sm text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white cursor-pointer"
                title="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="flex items-center justify-between lg:justify-end gap-3 text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium">
              <Filter className="w-3.5 h-3.5 text-blue-400" />
              Showing <strong className="text-white">{filteredRecords.length}</strong> of{' '}
              <strong className="text-white">{records.length}</strong> searches
            </span>
            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-blue-400 border border-slate-800 font-semibold cursor-pointer transition"
              >
                Reset Filters
              </button>
            )}
          </div>
        </div>

        {/* Filter Controls: Business Category, Country, State, City, From Date, To Date */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 pt-2 border-t border-slate-800/80">
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">
              Business Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="all">All Categories</option>
              {filterOptions.categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">
              Country
            </label>
            <select
              value={selectedCountry}
              onChange={(e) => {
                setSelectedCountry(e.target.value);
                setSelectedState('all');
                setSelectedCity('all');
              }}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="all">All Countries</option>
              {filterOptions.countries.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">
              State / Region
            </label>
            <select
              value={selectedState}
              onChange={(e) => {
                setSelectedState(e.target.value);
                setSelectedCity('all');
              }}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="all">All States</option>
              {filterOptions.states.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">
              City
            </label>
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="all">All Cities</option>
              {filterOptions.cities.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">
              From Date
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">
              To Date
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
      </div>

      {/* Error Message Banner */}
      {error && (
        <div className="glass-panel p-4 border border-red-500/30 bg-red-500/10 text-red-400 text-xs sm:text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading Indicator */}
      {isLoading ? (
        <div className="glass-panel p-12 text-center">
          <div className="w-9 h-9 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm font-bold text-slate-200">Loading your search history...</p>
        </div>
      ) : filteredRecords.length === 0 ? (
        /* Clean Empty State */
        <div className="glass-panel p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-blue-400">
            <Clock className="w-6 h-6" />
          </div>
          <h2 className="text-base font-bold text-white">
            {records.length === 0
              ? 'No Previous Searches Found'
              : 'No Search Records Match Your Filters'}
          </h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
            {records.length === 0
              ? 'When you run opportunity discovery analyses, your searches and generated business opportunities will be automatically archived here.'
              : 'Try clearing or adjusting your keyword, date, location, or category filters to view more history records.'}
          </p>
          <div className="pt-2 flex justify-center gap-3">
            {hasActiveFilters ? (
              <button
                type="button"
                onClick={handleResetFilters}
                className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-blue-400 border border-slate-800 cursor-pointer transition"
              >
                Reset All Filters
              </button>
            ) : (
              <button
                type="button"
                onClick={onNavigateDiscover}
                className="btn-primary-text px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-xs font-bold text-white flex items-center gap-1.5 cursor-pointer transition shadow-sm"
              >
                <Compass className="w-4 h-4 text-white" />
                <span className="text-white">Run Your First Search</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        /* Reverse-Chronological History List */
        <div className="space-y-4">
          {displayedRecords.map((sh) => {
            const opps = sh.opportunities || [];
            const oppCount = opps.length;
            const isExpanded = expandedId === sh.id;
            const isLiveStatus =
              sh.data_status_label &&
              sh.data_status_label.toLowerCase().includes('live');

            return (
              <div
                key={sh.id}
                className="glass-panel glass-panel-hover p-5 space-y-4 transition"
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Left: Category, Location, Date/Time & Search Filters Used */}
                  <div
                    onClick={() => onSelectHistorySearch && onSelectHistorySearch(sh)}
                    className="space-y-2 cursor-pointer flex-1"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-500/15 text-blue-400 border border-blue-500/30 flex items-center gap-1">
                        <Layers className="w-3 h-3" />
                        {sh.domain || 'General Business'}
                      </span>

                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        {oppCount} {oppCount === 1 ? 'Opportunity' : 'Opportunities'} Generated
                      </span>

                      {sh.data_status_label && (
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${
                            isLiveStatus
                              ? 'bg-teal-500/15 text-teal-400 border-teal-500/30'
                              : 'bg-slate-900 text-slate-400 border-slate-800'
                          }`}
                        >
                          {sh.data_status_label}
                        </span>
                      )}

                      <span className="text-xs text-slate-400 flex items-center gap-1 ml-auto lg:ml-0">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        {formatDateTime(sh.created_at)}
                      </span>
                    </div>

                    {/* Location Hierarchy: Area, City, State, Country */}
                    <div className="flex flex-wrap items-center gap-2 text-sm sm:text-base font-extrabold text-white hover:text-blue-400 transition">
                      <MapPin className="w-4 h-4 text-blue-400 shrink-0" />
                      <span>
                        {sh.area}, {sh.city}, {sh.state || '—'} ({sh.country || 'India'})
                      </span>
                    </div>

                    {/* Search Filters Used & Optional Search Keyword */}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-400">
                      <span className="inline-flex items-center gap-1">
                        <Wallet className="w-3.5 h-3.5 text-blue-400" />
                        Budget:{' '}
                        <strong className="text-slate-200">
                          {sh.currency || 'INR'} {Number(sh.budget || 0).toLocaleString()}
                        </strong>
                      </span>

                      <span className="inline-flex items-center gap-1">
                        <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-400" />
                        Experience:{' '}
                        <strong className="text-slate-200">
                          {sh.experience_level || 'Beginner'}
                        </strong>
                      </span>

                      <span>
                        Risk Preference:{' '}
                        <strong className="text-slate-200">
                          {sh.risk_preference || 'Low'}
                        </strong>
                      </span>

                      {sh.user_query && sh.user_query.trim() && (
                        <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-slate-300">
                          Keyword: &ldquo;{sh.user_query}&rdquo;
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Right Action Buttons: Preview Toggle, View Results, Delete */}
                  <div className="flex flex-wrap items-center gap-2 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-800/80">
                    {oppCount > 0 && (
                      <button
                        type="button"
                        onClick={() => setExpandedId(isExpanded ? null : sh.id)}
                        className="px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-300 border border-slate-800 flex items-center gap-1 cursor-pointer transition"
                      >
                        <span>{isExpanded ? 'Hide Preview' : 'Preview Ideas'}</span>
                        {isExpanded ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
                        )}
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={() => onSelectHistorySearch && onSelectHistorySearch(sh)}
                      className="btn-primary-text px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-xs font-bold text-white flex items-center gap-1.5 cursor-pointer transition shadow-sm"
                    >
                      <span className="text-white">View Results</span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-white" />
                    </button>

                    <button
                      type="button"
                      onClick={() => setRecordToDelete(sh)}
                      title="Delete this search history record"
                      className="p-2 rounded-xl bg-slate-900 hover:bg-red-500/15 text-slate-400 hover:text-red-400 border border-slate-800 hover:border-red-500/30 cursor-pointer transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Expandable Opportunity Results Preview */}
                {isExpanded && oppCount > 0 && (
                  <div className="pt-3 border-t border-slate-800 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {opps.map((opp, idx) => (
                      <div
                        key={opp.id || idx}
                        onClick={() =>
                          onSelectOpportunity
                            ? onSelectOpportunity(opp)
                            : onSelectHistorySearch && onSelectHistorySearch(sh)
                        }
                        className="p-3 rounded-xl bg-slate-900/80 hover:bg-slate-800/80 border border-slate-800 flex items-start justify-between gap-2.5 cursor-pointer transition"
                      >
                        <div className="min-w-0">
                          <div className="text-xs font-bold text-white truncate">
                            {opp.title}
                          </div>
                          <div className="text-[11px] text-slate-400 mt-0.5 truncate">
                            {opp.category} &bull;{' '}
                            {opp.startupBudget?.total_formatted || 'View Budget'}
                          </div>
                        </div>
                        <span className="px-2 py-0.5 rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[11px] font-bold shrink-0">
                          {opp.score || 80}/100
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {/* Pagination / Load More Footer */}
          {hasMore && (
            <div className="flex flex-col items-center justify-center pt-2 gap-2">
              <button
                type="button"
                onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}
                className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-bold text-blue-400 border border-slate-800 hover:border-blue-500/40 cursor-pointer transition shadow-sm"
              >
                Load More Searches ({filteredRecords.length - visibleCount} remaining)
              </button>
              <span className="text-[11px] text-slate-400">
                Displaying {displayedRecords.length} of {filteredRecords.length} matching records
              </span>
            </div>
          )}
        </div>
      )}

      {/* Confirmation Dialog Modal Before Deleting a History Record */}
      {recordToDelete && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/75 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget && !isDeleting) {
              setRecordToDelete(null);
            }
          }}
        >
          <div className="glass-panel w-full max-w-md p-6 space-y-4 border border-slate-700 shadow-2xl">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-red-600/15 border border-red-500/30 flex items-center justify-center text-red-400 shrink-0">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    Delete Search History Record?
                  </h3>
                  <p className="text-xs text-slate-400">
                    This action will permanently remove this record from your history.
                  </p>
                </div>
              </div>
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => setRecordToDelete(null)}
                className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs space-y-1">
              <div className="font-bold text-white">
                {recordToDelete.area}, {recordToDelete.city}, {recordToDelete.state} (
                {recordToDelete.country})
              </div>
              <div className="text-slate-400">
                Category: <strong className="text-slate-200">{recordToDelete.domain}</strong> &bull;{' '}
                {(recordToDelete.opportunities || []).length} opportunities
              </div>
              <div className="text-slate-400">
                Date: {formatDateTime(recordToDelete.created_at)}
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => setRecordToDelete(null)}
                className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-300 border border-slate-800 cursor-pointer transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isDeleting}
                onClick={handleConfirmDelete}
                className="btn-primary-text px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-xs font-bold text-white flex items-center gap-1.5 cursor-pointer transition shadow-sm"
              >
                <Trash2 className="w-3.5 h-3.5 text-white" />
                <span className="text-white">
                  {isDeleting ? 'Deleting...' : 'Confirm Delete'}
                </span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
