import React, { useState, useEffect, useCallback } from 'react';
import TopNav from './components/TopNav';
import CompareModal from './components/CompareModal';
import DashboardPage from './pages/DashboardPage';
import DiscoverPage from './pages/DiscoverPage';
import HistoryPage from './pages/HistoryPage';
import ReportDetailPage from './pages/ReportDetailPage';
import MarketTrendsPage from './pages/MarketTrendsPage';
import SavedReportsPage from './pages/SavedReportsPage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import {
  checkHealth,
  getCategories,
  getCountries,
  getDashboardData,
  discoverOpportunities,
  saveOpportunityReport,
  getSavedReports,
  deleteSavedReport,
  getSearchHistory,
} from './services/api';

export default function App() {
  // User session (defaults to an active workspace user so dashboard works immediately, with optional OTP login)
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('biof_user');
      return saved ? JSON.parse(saved) : { email: 'founder@opportunity.ai' };
    } catch {
      return { email: 'founder@opportunity.ai' };
    }
  });
  const [showLoginModal, setShowLoginModal] = useState(false);

  // Navigation tab: 'dashboard' | 'discover' | 'trends' | 'saved' | 'settings' | 'report_detail'
  const [activeTab, setActiveTab] = useState('dashboard');
  const [previousTab, setPreviousTab] = useState('dashboard');

  // Application state
  const [healthData, setHealthData] = useState(null);
  const [countries, setCountries] = useState([]);
  const [categoriesData, setCategoriesData] = useState({});
  const [dashboardData, setDashboardData] = useState(null);

  // Active discovery & report states
  const [discoveryResult, setDiscoveryResult] = useState(null);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoverError, setDiscoverError] = useState('');
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);

  // Saved reports, history & comparison state
  const [savedReports, setSavedReports] = useState([]);
  const [searchHistory, setSearchHistory] = useState([]);
  const [compareList, setCompareList] = useState([]);
  const [showCompareModal, setShowCompareModal] = useState(false);

  const refreshWorkspace = useCallback(async () => {
    const email = currentUser?.email || 'founder@opportunity.ai';
    try {
      const [dash, savedRes, histRes] = await Promise.all([
        getDashboardData(email),
        getSavedReports(email),
        getSearchHistory(email),
      ]);
      setDashboardData(dash);
      setSavedReports(savedRes.reports || []);
      setSearchHistory(histRes || []);
    } catch (err) {
      console.error('Error refreshing workspace:', err);
    }
  }, [currentUser?.email]);

  // Initial load of metadata and dashboard
  useEffect(() => {
    async function initApp() {
      try {
        const [hlth, cntries, cats] = await Promise.all([
          checkHealth(),
          getCountries(),
          getCategories(),
        ]);
        setHealthData(hlth);
        setCountries(cntries.countries || []);
        setCategoriesData(cats || {});
      } catch (err) {
        console.error('Failed to load initial metadata:', err);
      }
      await refreshWorkspace();
    }
    initApp();
  }, [refreshWorkspace]);

  // Handle running a new Opportunity Discovery search
  const handleDiscover = async (formPayload) => {
    setIsDiscovering(true);
    setDiscoverError('');
    try {
      const res = await discoverOpportunities({
        ...formPayload,
        email: currentUser?.email || 'founder@opportunity.ai',
      });
      setDiscoveryResult(res);
      await refreshWorkspace();
    } catch (err) {
      setDiscoverError(err.message || 'Discovery failed. Please check your inputs.');
    } finally {
      setIsDiscovering(false);
    }
  };

  // Handle opening a full report
  const handleSelectOpportunity = (opp) => {
    if (!opp) return;
    setPreviousTab(activeTab === 'report_detail' ? 'discover' : activeTab);
    setSelectedOpportunity(opp);
    setActiveTab('report_detail');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handle saving a report to SQLite
  const handleSaveReport = async (opp) => {
    if (!opp) return;
    try {
      await saveOpportunityReport(currentUser?.email || 'founder@opportunity.ai', opp);
      await refreshWorkspace();
    } catch (err) {
      console.error('Failed to save report:', err);
    }
  };

  // Handle deleting a saved report
  const handleDeleteSavedReport = async (reportId) => {
    try {
      await deleteSavedReport(reportId, currentUser?.email || 'founder@opportunity.ai');
      await refreshWorkspace();
    } catch (err) {
      console.error('Failed to delete report:', err);
    }
  };

  // Handle toggling an opportunity in the comparison tray
  const handleToggleCompare = (opp) => {
    if (!opp) return;
    setCompareList((prev) => {
      const exists = prev.some((item) => item.id === opp.id);
      if (exists) {
        return prev.filter((item) => item.id !== opp.id);
      }
      if (prev.length >= 4) {
        return [...prev.slice(1), opp];
      }
      return [...prev, opp];
    });
  };

  // Handle loading a historical search from SQLite
  const handleSelectHistorySearch = (histItem) => {
    if (!histItem) return;
    setDiscoveryResult({
      country: histItem.country || 'India',
      state: histItem.state || 'Karnataka',
      city: histItem.city,
      area: histItem.area,
      category: histItem.domain,
      currency: histItem.currency || 'INR',
      budget: histItem.budget || 300000,
      budget_formatted: `${histItem.currency || 'INR'} ${Number(
        histItem.budget || 300000
      ).toLocaleString()}`,
      data_status_label: histItem.data_status_label || 'Archived Search',
      nlp_summary: histItem.nlp_summary || null,
      opportunities: histItem.opportunities || [],
    });
    setActiveTab('discover');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const compareIds = compareList.map((c) => c.id);

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav
        activeTab={activeTab === 'report_detail' ? previousTab : activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        userEmail={currentUser?.email}
        onLogout={() => setShowLoginModal(true)}
        compareList={compareList}
        onOpenCompare={() => setShowCompareModal(true)}
        systemStatus={dashboardData?.system_status}
      />

      <main className="flex-1 max-w-[1440px] w-full mx-auto px-4 sm:px-6 py-6">
        {activeTab === 'dashboard' && (
          <DashboardPage
            dashboardData={dashboardData}
            onNavigate={(tab) => setActiveTab(tab)}
            onSelectOpportunity={handleSelectOpportunity}
            onSaveReport={handleSaveReport}
            onToggleCompare={handleToggleCompare}
            compareIds={compareIds}
            onSelectHistorySearch={handleSelectHistorySearch}
          />
        )}

        {activeTab === 'discover' && (
          <DiscoverPage
            countries={countries}
            categoriesData={categoriesData}
            onDiscover={handleDiscover}
            isLoading={isDiscovering}
            error={discoverError}
            discoveryResult={discoveryResult}
            onSelectOpportunity={handleSelectOpportunity}
            onSaveReport={handleSaveReport}
            onToggleCompare={handleToggleCompare}
            compareIds={compareIds}
          />
        )}

        {activeTab === 'history' && (
          <HistoryPage
            userEmail={currentUser?.email || 'founder@opportunity.ai'}
            initialHistory={searchHistory}
            onSelectHistorySearch={handleSelectHistorySearch}
            onSelectOpportunity={handleSelectOpportunity}
            onNavigateDiscover={() => setActiveTab('discover')}
            onHistoryChanged={refreshWorkspace}
          />
        )}

        {activeTab === 'report_detail' && (
          <ReportDetailPage
            opportunity={selectedOpportunity}
            onBack={() => setActiveTab(previousTab || 'dashboard')}
            onSaveReport={handleSaveReport}
            onToggleCompare={handleToggleCompare}
            isCompared={
              selectedOpportunity ? compareIds.includes(selectedOpportunity.id) : false
            }
          />
        )}

        {activeTab === 'trends' && (
          <MarketTrendsPage
            dashboardData={dashboardData}
            discoveryResult={discoveryResult}
          />
        )}

        {activeTab === 'saved' && (
          <SavedReportsPage
            savedReports={savedReports}
            onSelectOpportunity={handleSelectOpportunity}
            onDeleteSavedReport={handleDeleteSavedReport}
            onToggleCompare={handleToggleCompare}
            compareIds={compareIds}
            onNavigateDiscover={() => setActiveTab('discover')}
          />
        )}

        {activeTab === 'settings' && (
          <SettingsPage
            healthData={healthData}
            userEmail={currentUser?.email}
            onOpenLoginModal={() => setShowLoginModal(true)}
          />
        )}
      </main>

      {/* Side-by-Side Comparison Modal */}
      {showCompareModal && (
        <CompareModal
          opportunities={compareList}
          onClose={() => setShowCompareModal(false)}
          onRemoveFromCompare={(id) =>
            setCompareList((prev) => prev.filter((item) => item.id !== id))
          }
          onSelectOpportunity={handleSelectOpportunity}
        />
      )}

      {/* Optional Email OTP Login Modal */}
      {showLoginModal && (
        <LoginPage
          onLoginSuccess={(user) => {
            setCurrentUser(user);
            localStorage.setItem('biof_user', JSON.stringify(user));
            setShowLoginModal(false);
          }}
          onCancel={() => setShowLoginModal(false)}
        />
      )}
    </div>
  );
}
