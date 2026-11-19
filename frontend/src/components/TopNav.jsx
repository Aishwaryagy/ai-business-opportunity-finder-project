import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Compass,
  Clock,
  TrendingUp,
  BookmarkCheck,
  Settings,
  Sparkles,
  LogOut,
  GitCompare,
  Sun,
  Moon,
} from 'lucide-react';

export default function TopNav({
  activeTab,
  onSelectTab,
  userEmail,
  onLogout,
  compareList = [],
  onOpenCompare,
}) {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('oppfinder_theme') || 'dark';
    } catch {
      return 'dark';
    }
  });

  useEffect(() => {
    const isLight = theme === 'light';
    document.body.classList.toggle('light-mode', isLight);
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem('oppfinder_theme', theme);
    } catch {
      // Ignore storage errors
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      iconBadge: 'bg-blue-600 text-white shadow-sm',
      activePill: 'bg-blue-600/20 text-white border-blue-500/60 shadow-sm',
      hoverPill: 'hover:border-slate-700 hover:bg-slate-800/70',
      glowBar: 'bg-blue-500',
    },
    {
      id: 'discover',
      label: 'Discover Opportunities',
      icon: Compass,
      iconBadge: 'bg-teal-600 text-white shadow-sm',
      activePill: 'bg-teal-600/20 text-white border-teal-500/60 shadow-sm',
      hoverPill: 'hover:border-slate-700 hover:bg-slate-800/70',
      glowBar: 'bg-teal-500',
    },
    {
      id: 'history',
      label: 'History',
      icon: Clock,
      iconBadge: 'bg-emerald-600 text-white shadow-sm',
      activePill: 'bg-emerald-600/20 text-white border-emerald-500/60 shadow-sm',
      hoverPill: 'hover:border-slate-700 hover:bg-slate-800/70',
      glowBar: 'bg-emerald-500',
    },
    {
      id: 'trends',
      label: 'Market Trends & NLP',
      icon: TrendingUp,
      iconBadge: 'bg-indigo-600 text-white shadow-sm',
      activePill: 'bg-indigo-600/20 text-white border-indigo-500/60 shadow-sm',
      hoverPill: 'hover:border-slate-700 hover:bg-slate-800/70',
      glowBar: 'bg-indigo-500',
    },
    {
      id: 'saved',
      label: 'Saved Reports',
      icon: BookmarkCheck,
      iconBadge: 'bg-amber-600 text-white shadow-sm',
      activePill: 'bg-amber-600/20 text-white border-amber-500/60 shadow-sm',
      hoverPill: 'hover:border-slate-700 hover:bg-slate-800/70',
      glowBar: 'bg-amber-500',
    },
    {
      id: 'settings',
      label: 'Settings & Status',
      icon: Settings,
      iconBadge: 'bg-slate-700 text-white shadow-sm',
      activePill: 'bg-slate-700/40 text-white border-slate-500/60 shadow-sm',
      hoverPill: 'hover:border-slate-700 hover:bg-slate-800/70',
      glowBar: 'bg-slate-400',
    },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800 bg-[#0F172A]/95 backdrop-blur-md shadow-sm no-print">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Brand Logo & Name */}
        <div
          onClick={() => onSelectTab('dashboard')}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-sm group-hover:bg-blue-700 transition-colors">
            <Sparkles className="w-5 h-5 text-white" strokeWidth={2.2} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-extrabold tracking-tight text-white">
              Opportunity Intelligence
            </span>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30">
              Global Edition
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto py-1 px-2 rounded-2xl bg-slate-900 border border-slate-800">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelectTab(item.id)}
                className={`relative group flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer border ${
                  active
                    ? item.activePill
                    : `text-slate-300 border-transparent bg-slate-900/50 hover:text-white ${item.hoverPill}`
                }`}
              >
                <span
                  className={`w-7 h-7 rounded-lg flex items-center justify-center transition-transform duration-200 ${item.iconBadge}`}
                >
                  <Icon className="w-4 h-4 text-white" strokeWidth={2.2} />
                </span>
                <span className="tracking-tight">{item.label}</span>
                {active && (
                  <span
                    className={`absolute -bottom-1 left-4 right-4 h-0.5 rounded-full ${item.glowBar}`}
                  />
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Side Compare Button, Theme Switch & User Profile */}
        <div className="flex items-center gap-2.5">
          {/* Compare Selected Opportunities Button */}
          {compareList.length > 0 && (
            <button
              type="button"
              onClick={onOpenCompare}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white border border-blue-500 transition cursor-pointer shadow-sm"
            >
              <GitCompare className="w-3.5 h-3.5" strokeWidth={2.2} />
              <span>Compare ({compareList.length})</span>
            </button>
          )}

          {/* Light / Dark Mode Comfort Toggle Switch */}
          <button
            type="button"
            onClick={toggleTheme}
            role="switch"
            aria-checked={theme === 'light'}
            title={
              theme === 'dark'
                ? 'Switch to Comfortable Light Mode'
                : 'Switch to Executive Dark Mode'
            }
            className="theme-toggle-btn relative flex items-center gap-2 px-2.5 py-1.5 rounded-full border border-slate-700 bg-slate-900 hover:border-blue-500 transition-all cursor-pointer shadow-sm"
          >
            <div className="relative flex items-center w-14 h-7 rounded-full p-0.5 bg-slate-950 border border-slate-800 theme-toggle-track transition-colors">
              {/* Sliding Thumb */}
              <span
                className={`w-6 h-6 rounded-full flex items-center justify-center transition-all duration-300 transform shadow-sm ${
                  theme === 'light'
                    ? 'translate-x-7 bg-amber-500 text-white'
                    : 'translate-x-0 bg-blue-600 text-white'
                }`}
              >
                {theme === 'light' ? (
                  <Sun className="w-3.5 h-3.5 text-white" strokeWidth={2.4} />
                ) : (
                  <Moon className="w-3.5 h-3.5 text-white" strokeWidth={2.4} />
                )}
              </span>
              {/* Subtle Opposite Indicator Icon */}
              <span
                className={`absolute ${
                  theme === 'light' ? 'left-1.5 text-slate-400' : 'right-1.5 text-amber-400/80'
                } pointer-events-none transition-opacity`}
              >
                {theme === 'light' ? (
                  <Moon className="w-3 h-3" strokeWidth={2} />
                ) : (
                  <Sun className="w-3 h-3" strokeWidth={2} />
                )}
              </span>
            </div>
            <span className="hidden sm:inline text-xs font-bold tracking-tight pr-1 text-slate-200">
              {theme === 'light' ? 'Light' : 'Dark'}
            </span>
          </button>

          {/* User Badge */}
          {userEmail && (
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-200 shadow-sm">
              <div className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-[11px]">
                {userEmail.charAt(0).toUpperCase()}
              </div>
              <span className="max-w-[140px] truncate font-medium">{userEmail}</span>
            </div>
          )}

          {onLogout && (
            <button
              type="button"
              onClick={onLogout}
              title="Switch user or sign out"
              className="p-2 rounded-xl bg-slate-900 hover:bg-red-600 text-slate-300 hover:text-white border border-slate-700 hover:border-red-500 transition cursor-pointer shadow-sm"
            >
              <LogOut className="w-4 h-4" strokeWidth={2.2} />
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
