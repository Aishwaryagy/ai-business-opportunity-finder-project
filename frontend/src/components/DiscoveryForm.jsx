import React, { useState, useEffect, useMemo } from 'react';
import {
  Globe,
  MapPin,
  Wallet,
  Briefcase,
  Sparkles,
  ArrowRightLeft,
  ShieldCheck,
  UserCheck,
  Search,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { getCurrencies, convertCurrency } from '../services/api';

export default function DiscoveryForm({
  countries = [],
  categoriesData = {},
  onSubmit,
  isLoading,
}) {
  // Location states
  const [countrySearch, setCountrySearch] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('India');
  const [selectedState, setSelectedState] = useState('Karnataka');
  const [selectedCity, setSelectedCity] = useState('Shivamogga');
  const [selectedArea, setSelectedArea] = useState('Gandhi Nagar');
  const [customAreaMode, setCustomAreaMode] = useState(false);
  const [customAreaText, setCustomAreaText] = useState('');

  // Business & Budget states
  const [selectedCategory, setSelectedCategory] = useState('Daily Needs & Grocery');
  const [currency, setCurrency] = useState('INR');
  const [currencyMeta, setCurrencyMeta] = useState(null);
  const [budget, setBudget] = useState(500000);
  const [activePreset, setActivePreset] = useState('medium');
  const [targetCurrency, setTargetCurrency] = useState('USD');
  const [conversionPreview, setConversionPreview] = useState(null);
  const [isConverting, setIsConverting] = useState(false);

  // Preferences
  const [businessType, setBusinessType] = useState('Flexible (Any suitable type)');
  const [experienceLevel, setExperienceLevel] = useState('Beginner');
  const [riskPreference, setRiskPreference] = useState('Low');
  const [recommendEveryday, setRecommendEveryday] = useState(true);
  const [skillsAndInterests, setSkillsAndInterests] = useState('');
  const [formError, setFormError] = useState('');

  // Filtered countries for searchable selector
  const filteredCountries = useMemo(() => {
    if (!countrySearch.trim()) return countries;
    const q = countrySearch.toLowerCase();
    return countries.filter(
      (c) =>
        c.country.toLowerCase().includes(q) ||
        c.iso_code.toLowerCase().includes(q) ||
        c.currency.toLowerCase().includes(q)
    );
  }, [countries, countrySearch]);

  // Active country object
  const activeCountryObj = useMemo(() => {
    return (
      countries.find((c) => c.country === selectedCountry) ||
      countries[0] || {
        country: 'India',
        iso_code: 'IN',
        currency: 'INR',
        currency_symbol: '₹',
        currency_name: 'Indian Rupee',
        states: {
          Karnataka: {
            Shivamogga: ['Gandhi Nagar', 'Vinoba Nagar', 'Gopi Circle'],
          },
        },
      }
    );
  }, [countries, selectedCountry]);

  // Available states for selected country
  const availableStates = useMemo(() => {
    return Object.keys(activeCountryObj?.states || {});
  }, [activeCountryObj]);

  // Available cities for selected state
  const availableCities = useMemo(() => {
    const stateObj = (activeCountryObj?.states || {})[selectedState] || {};
    return Object.keys(stateObj);
  }, [activeCountryObj, selectedState]);

  // Available areas for selected city
  const availableAreas = useMemo(() => {
    const stateObj = (activeCountryObj?.states || {})[selectedState] || {};
    return stateObj[selectedCity] || [];
  }, [activeCountryObj, selectedState, selectedCity]);

  // Load currency presets when currency changes
  useEffect(() => {
    let active = true;
    async function loadCurrMeta() {
      try {
        const res = await getCurrencies(currency);
        if (active && res.currency) {
          setCurrencyMeta(res.currency);
          const med =
            res.currency.presets?.find((p) => p.id === 'medium') ||
            res.currency.presets?.[0];
          if (med) {
            setBudget(med.default);
            setActivePreset(med.id);
          }
        }
      } catch (e) {
        console.error('Failed to load currency presets:', e);
      }
    }
    loadCurrMeta();
    return () => {
      active = false;
    };
  }, [currency]);

  // Handle Country Change -> Reset State, City, Area, and auto-set official ISO-4217 currency
  const handleCountryChange = (newCountryName) => {
    setSelectedCountry(newCountryName);
    const found = countries.find((c) => c.country === newCountryName);
    if (found) {
      setCurrency(found.currency);
      if (found.currency === 'USD') {
        setTargetCurrency('EUR');
      } else {
        setTargetCurrency('USD');
      }
      const stList = Object.keys(found.states || {});
      const firstState = stList[0] || '';
      setSelectedState(firstState);
      const cityList = firstState ? Object.keys(found.states[firstState] || {}) : [];
      const firstCity = cityList[0] || '';
      setSelectedCity(firstCity);
      const areaList =
        firstState && firstCity ? found.states[firstState][firstCity] || [] : [];
      if (areaList.length > 0) {
        setSelectedArea(areaList[0]);
        setCustomAreaMode(false);
      } else {
        setSelectedArea('');
        setCustomAreaMode(true);
      }
    }
    setConversionPreview(null);
  };

  // Handle State Change -> Reset City & Area
  const handleStateChange = (newState) => {
    setSelectedState(newState);
    const stateMap = (activeCountryObj?.states || {})[newState] || {};
    const cityList = Object.keys(stateMap);
    const firstCity = cityList[0] || '';
    setSelectedCity(firstCity);
    const areaList = firstCity ? stateMap[firstCity] || [] : [];
    if (areaList.length > 0) {
      setSelectedArea(areaList[0]);
      setCustomAreaMode(false);
    } else {
      setSelectedArea('');
      setCustomAreaMode(true);
    }
  };

  // Handle City Change -> Reset Area
  const handleCityChange = (newCity) => {
    setSelectedCity(newCity);
    const stateMap = (activeCountryObj?.states || {})[selectedState] || {};
    const areaList = stateMap[newCity] || [];
    if (areaList.length > 0) {
      setSelectedArea(areaList[0]);
      setCustomAreaMode(false);
    } else {
      setSelectedArea('');
      setCustomAreaMode(true);
    }
  };

  // Live Currency Conversion Preview
  const handleConvertPreview = async () => {
    if (!budget || Number(budget) <= 0) return;
    setIsConverting(true);
    try {
      const res = await convertCurrency({
        amount: Number(budget),
        fromCurrency: currency,
        toCurrency: targetCurrency,
      });
      setConversionPreview(res);
    } catch (err) {
      setFormError(err.message);
    } finally {
      setIsConverting(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setFormError('');

    const finalArea = customAreaMode ? customAreaText.trim() : selectedArea.trim();
    if (!selectedCountry || !selectedState || !selectedCity) {
      setFormError('Please select a Country, State/Province, and City.');
      return;
    }
    if (!finalArea) {
      setFormError('Please select or enter a local neighbourhood/area.');
      return;
    }
    if (!budget || Number(budget) <= 0) {
      setFormError('Please enter a valid positive startup budget.');
      return;
    }

    onSubmit({
      country: selectedCountry,
      state: selectedState,
      city: selectedCity,
      area: finalArea,
      category: selectedCategory,
      budget: Number(budget),
      currency,
      target_currency: targetCurrency,
      business_type: businessType,
      experience_level: experienceLevel,
      risk_preference: riskPreference,
      recommend_everyday_simple: recommendEveryday,
      skills_and_interests: skillsAndInterests.trim(),
    });
  };

  const categories = categoriesData.categories || [
    { id: 'Daily Needs & Grocery', label: 'Daily Needs, Dairy & Grocery' },
    { id: 'Food & Beverage', label: 'Tiffin, Bakery, Tea/Coffee & Food' },
    { id: 'Home & Personal Services', label: 'Laundry, Cleaning, Tailoring & Salon' },
    { id: 'Repair & Local Retail', label: 'Mobile Repair, Water Delivery & Retail' },
    { id: 'Education & Tutoring', label: 'Tutoring, Coaching & Skill Centers' },
    { id: 'Logistics & Delivery', label: 'Local Delivery & Courier Services' },
    { id: 'Agri & Fresh Produce', label: 'Small Farming & Produce Distribution' },
    { id: 'Sustainability & Recycling', label: 'Small-Scale Recycling & Refill Products' },
    { id: 'Explore All Categories', label: 'Explore All (Recommend Best Fit)' },
  ];

  const businessTypes = categoriesData.business_types || [
    'Flexible (Any suitable type)',
    'Shop / Storefront',
    'Home-based',
    'Service-based',
    'Food / Kitchen',
    'Retail / Kiosk',
    'Online / Hybrid',
  ];

  const presets = currencyMeta?.presets || [];

  return (
    <form onSubmit={handleSubmit} className="glass-panel p-6 sm:p-8 space-y-6">
      {/* Header Banner inside Form */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div>
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-blue-500">
            <Sparkles className="w-3.5 h-3.5" />
            Opportunity Discovery Parameters
          </span>
          <h2 className="text-xl sm:text-2xl font-bold text-white mt-0.5 tracking-tight">
            Configure Target Location, Capital &amp; Business Profile
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Select your target market hierarchy and startup budget to generate data-backed opportunity reports.
          </p>
        </div>

        {/* Selected Country ISO & Official Currency Badge */}
        <div className="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-slate-900/70 border border-slate-800">
          <Globe className="w-4 h-4 text-blue-400" />
          <div className="text-xs">
            <div className="text-[11px] text-slate-400">Active Jurisdiction</div>
            <div className="font-semibold text-white">
              {activeCountryObj.country} ({activeCountryObj.iso_code}) &bull;{' '}
              <span className="text-blue-400">
                {activeCountryObj.currency} ({activeCountryObj.currency_symbol})
              </span>
            </div>
          </div>
        </div>
      </div>

      {formError && (
        <div className="p-3.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs sm:text-sm flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{formError}</span>
        </div>
      )}

      {/* SECTION 1: CASCADING GLOBAL LOCATION SELECTOR */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-blue-400" />
            1. Geographic Market Selection
          </h3>
          <span className="text-[11px] text-slate-400 hidden sm:inline">
            Country &rarr; State/Province &rarr; City &rarr; Local Area
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 1. Country with search filter */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-300">
              Country (ISO-3166)
            </label>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Filter country or currency..."
                value={countrySearch}
                onChange={(e) => setCountrySearch(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <select
              value={selectedCountry}
              onChange={(e) => handleCountryChange(e.target.value)}
              disabled={isLoading}
              className="w-full h-10 px-3 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              {filteredCountries.map((c) => (
                <option key={c.iso_code} value={c.country}>
                  {c.country} ({c.iso_code}) — {c.currency} ({c.currency_symbol})
                </option>
              ))}
            </select>
          </div>

          {/* 2. State / Province / Region */}
          <div className="space-y-1.5 flex flex-col justify-end">
            <label className="block text-xs font-semibold text-slate-300">
              State / Province / Region
            </label>
            <div className="text-[11px] text-slate-400">
              Regional administrative jurisdiction
            </div>
            <select
              value={selectedState}
              onChange={(e) => handleStateChange(e.target.value)}
              disabled={isLoading}
              className="w-full h-10 px-3 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              {availableStates.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>

          {/* 3. City / Town */}
          <div className="space-y-1.5 flex flex-col justify-end">
            <label className="block text-xs font-semibold text-slate-300">
              City or Municipality
            </label>
            <div className="text-[11px] text-slate-400">
              Target urban or regional center
            </div>
            <select
              value={selectedCity}
              onChange={(e) => handleCityChange(e.target.value)}
              disabled={isLoading}
              className="w-full h-10 px-3 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              {availableCities.map((ct) => (
                <option key={ct} value={ct}>
                  {ct}
                </option>
              ))}
            </select>
          </div>

          {/* 4. Local Area / Neighbourhood */}
          <div className="space-y-1.5 flex flex-col justify-end">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold text-slate-300">
                Local Neighbourhood
              </label>
              <button
                type="button"
                onClick={() => setCustomAreaMode(!customAreaMode)}
                className="text-[11px] font-medium text-blue-400 hover:underline cursor-pointer"
              >
                {customAreaMode ? 'Select from list' : 'Custom input'}
              </button>
            </div>
            <div className="text-[11px] text-slate-400">
              {customAreaMode
                ? 'Enter any commercial street or zone'
                : 'Verified micro-market locality'}
            </div>
            {customAreaMode ? (
              <input
                type="text"
                placeholder="e.g., Main Bazaar, Station Road..."
                value={customAreaText}
                onChange={(e) => setCustomAreaText(e.target.value)}
                className="w-full h-10 px-3 rounded-lg bg-slate-900 border border-blue-500/50 text-sm text-white focus:outline-none"
              />
            ) : (
              <select
                value={selectedArea}
                onChange={(e) => setSelectedArea(e.target.value)}
                disabled={isLoading}
                className="w-full h-10 px-3 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
              >
                {availableAreas.map((ar) => (
                  <option key={ar} value={ar}>
                    {ar}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      {/* SECTION 2: CURRENCY, STARTUP BUDGET & LIVE CONVERSION */}
      <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Wallet className="w-3.5 h-3.5 text-emerald-500" />
            2. Capital Allocation &amp; Currency ({currency} — {activeCountryObj.currency_symbol})
          </h3>
          <span className="text-xs text-slate-400">
            Choose a capital tier preset or specify exact startup funds
          </span>
        </div>

        {/* Budget Presets */}
        {presets.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {presets.map((p) => {
              const isSelected = activePreset === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    setActivePreset(p.id);
                    setBudget(p.default);
                    setConversionPreview(null);
                  }}
                  className={`p-3 rounded-lg border text-left transition cursor-pointer ${
                    isSelected
                      ? 'bg-blue-600/12 border-blue-500/40 text-blue-400'
                      : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="text-xs font-semibold text-white">{p.label}</div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    {activeCountryObj.currency_symbol}
                    {p.min.toLocaleString()} – {activeCountryObj.currency_symbol}
                    {p.max.toLocaleString()}
                  </div>
                </button>
              );
            })}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Available Startup Capital ({currency})
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-2.5 text-sm font-bold text-blue-400">
                {activeCountryObj.currency_symbol}
              </span>
              <input
                type="number"
                min={100}
                step="any"
                value={budget}
                onChange={(e) => {
                  setBudget(e.target.value);
                  setConversionPreview(null);
                }}
                className="w-full h-10 pl-10 pr-4 rounded-lg bg-slate-900 border border-slate-700 text-sm font-bold text-white focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              FX Reference Currency (Optional)
            </label>
            <div className="flex gap-2">
              <select
                value={targetCurrency}
                onChange={(e) => {
                  setTargetCurrency(e.target.value);
                  setConversionPreview(null);
                }}
                className="flex-1 h-10 px-3 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
              >
                {['USD', 'INR', 'EUR', 'GBP', 'JPY', 'AED', 'SGD', 'CAD', 'AUD'].map(
                  (c) => (
                    <option key={c} value={c}>
                      Convert to {c}
                    </option>
                  )
                )}
              </select>
              <button
                type="button"
                onClick={handleConvertPreview}
                disabled={isConverting}
                className="h-10 px-3.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 flex items-center gap-1.5 cursor-pointer transition"
              >
                <ArrowRightLeft className="w-3.5 h-3.5 text-blue-400" />
                <span>{isConverting ? '...' : 'Convert'}</span>
              </button>
            </div>
          </div>

          <div className="text-xs text-slate-300 bg-slate-900/70 p-2.5 rounded-lg border border-slate-800 min-h-[40px] flex items-center">
            {conversionPreview ? (
              <div>
                <div className="font-semibold text-emerald-400">
                  {conversionPreview.original_formatted} ={' '}
                  {conversionPreview.converted_formatted}
                </div>
                <div className="text-[11px] text-slate-400">
                  1 {conversionPreview.original_currency} = {conversionPreview.exchange_rate}{' '}
                  {conversionPreview.target_currency}
                </div>
              </div>
            ) : (
              <div className="text-[11px] text-slate-400">
                Click <strong>Convert</strong> to preview capital in {targetCurrency}.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* SECTION 3: CATEGORY, BUSINESS TYPE, EXPERIENCE & RISK */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Briefcase className="w-3.5 h-3.5 text-blue-400" />
          3. Sector, Operating Format &amp; Risk Profile
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Preferred Business Category */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Business Sector
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          {/* Preferred Business Type */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Operating Format
            </label>
            <select
              value={businessType}
              onChange={(e) => setBusinessType(e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              {businessTypes.map((bt) => (
                <option key={bt} value={bt}>
                  {bt}
                </option>
              ))}
            </select>
          </div>

          {/* Experience Level */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1">
              <UserCheck className="w-3.5 h-3.5 text-blue-400" />
              Operator Experience
            </label>
            <select
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              {['Beginner', 'Intermediate', 'Experienced'].map((exp) => (
                <option key={exp} value={exp}>
                  {exp}
                </option>
              ))}
            </select>
          </div>

          {/* Risk Preference */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              Risk Tolerance
            </label>
            <select
              value={riskPreference}
              onChange={(e) => setRiskPreference(e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              {['Low', 'Medium', 'High'].map((r) => (
                <option key={r} value={r}>
                  {r} Risk
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* SECTION 4: EVERYDAY BUSINESS TOGGLE & OPTIONAL SKILLS */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
        {/* Everyday Simple Businesses Toggle */}
        <div
          onClick={() => setRecommendEveryday(!recommendEveryday)}
          className={`lg:col-span-5 p-3.5 rounded-lg border cursor-pointer transition flex items-start gap-3 ${
            recommendEveryday
              ? 'bg-blue-600/10 border-blue-500/35'
              : 'bg-slate-900/50 border-slate-800'
          }`}
        >
          <input
            type="checkbox"
            checked={recommendEveryday}
            onChange={(e) => setRecommendEveryday(e.target.checked)}
            className="mt-0.5 w-4 h-4 accent-blue-600"
          />
          <div>
            <div className="text-xs font-semibold text-white flex items-center gap-1.5">
              Prioritize Proven Everyday Commercial Models
              <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
              Focuses on high-repeat local businesses (retail, food services, distribution,
              diagnostics, and essential services) with predictable unit economics.
            </p>
          </div>
        </div>

        {/* Optional Skills / Interests */}
        <div className="lg:col-span-7">
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Specific Assets, Skills, or Local Market Notes (Optional)
          </label>
          <input
            type="text"
            placeholder="e.g., Ground-floor commercial space available, or interest in morning dairy & tiffin distribution..."
            value={skillsAndInterests}
            onChange={(e) => setSkillsAndInterests(e.target.value)}
            className="w-full h-10 px-3.5 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Primary Action Button */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary-text w-full py-3.5 px-6 rounded-lg font-semibold text-sm text-white bg-blue-600 hover:bg-blue-500 shadow-sm flex items-center justify-center gap-2.5 transition cursor-pointer disabled:opacity-60"
        >
          <Sparkles className="w-4 h-4 text-white" />
          <span className="text-white">
            {isLoading
              ? 'Running Market Intelligence & VADER NLP Analysis...'
              : 'Generate Business Opportunities'}
          </span>
        </button>
      </div>
    </form>
  );
}
