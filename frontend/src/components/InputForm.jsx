import React, { useState, useEffect } from 'react';

export default function InputForm({
  domains = [],
  locations = {},
  onSubmit,
  isLoading
}) {
  const [selectedDomain, setSelectedDomain] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedArea, setSelectedArea] = useState('');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState('');

  // Set default domain once loaded
  useEffect(() => {
    if (domains.length > 0 && !selectedDomain) {
      // Prefer Education as first default or first in list
      const defaultDomain = domains.includes('Education') ? 'Education' : domains[0];
      setSelectedDomain(defaultDomain);
    }
  }, [domains, selectedDomain]);

  // Set default city and area once locations loaded
  useEffect(() => {
    const cities = Object.keys(locations);
    if (cities.length > 0 && !selectedCity) {
      const defaultCity = cities.includes('Bangalore') ? 'Bangalore' : cities[0];
      setSelectedCity(defaultCity);
      const areas = locations[defaultCity] || [];
      if (areas.length > 0) {
        setSelectedArea(areas[0]);
      }
    }
  }, [locations, selectedCity]);

  // When city changes, update available areas
  const handleCityChange = (e) => {
    const newCity = e.target.value;
    setSelectedCity(newCity);
    const availableAreas = locations[newCity] || [];
    if (availableAreas.length > 0) {
      setSelectedArea(availableAreas[0]);
    } else {
      setSelectedArea('');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setFormError('');

    if (!selectedDomain) {
      setFormError('Please select a business domain or choose "Explore for me".');
      return;
    }
    if (!selectedCity) {
      setFormError('Please select a city.');
      return;
    }
    if (!selectedArea) {
      setFormError('Please select a locality/area.');
      return;
    }

    onSubmit({
      domain: selectedDomain,
      city: selectedCity,
      area: selectedArea,
      description: description.trim()
    });
  };

  const availableAreas = locations[selectedCity] || [];

  return (
    <form className="card-glass" onSubmit={handleSubmit}>
      {formError && (
        <div className="error-alert">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{formError}</span>
        </div>
      )}

      <div className="form-grid">
        {/* Domain selection */}
        <div className="form-group">
          <label className="form-label" htmlFor="domain-select">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
            Business Domain
          </label>
          <select
            id="domain-select"
            className="form-control"
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            disabled={isLoading}
          >
            {domains.map((dom) => (
              <option key={dom} value={dom}>
                {dom === 'Explore for me' ? '✨ Explore for me (Auto-Infer)' : dom}
              </option>
            ))}
          </select>
          <span className="form-helper">
            {selectedDomain === 'Explore for me'
              ? 'Our engine discovers high-potential sectors automatically'
              : 'Select your preferred industry focus'}
          </span>
        </div>

        {/* City selection */}
        <div className="form-group">
          <label className="form-label" htmlFor="city-select">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
            City
          </label>
          <select
            id="city-select"
            className="form-control"
            value={selectedCity}
            onChange={handleCityChange}
            disabled={isLoading}
          >
            {Object.keys(locations).map((cityName) => (
              <option key={cityName} value={cityName}>
                {cityName}
              </option>
            ))}
          </select>
          <span className="form-helper">Geographic metropolitan focus</span>
        </div>

        {/* Area selection (Dynamic) */}
        <div className="form-group">
          <label className="form-label" htmlFor="area-select">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
            </svg>
            Area / Locality
          </label>
          <select
            id="area-select"
            className="form-control"
            value={selectedArea}
            onChange={(e) => setSelectedArea(e.target.value)}
            disabled={isLoading || availableAreas.length === 0}
          >
            {availableAreas.map((areaName) => (
              <option key={areaName} value={areaName}>
                {areaName}
              </option>
            ))}
          </select>
          <span className="form-helper">Dynamic micro-market clusters</span>
        </div>
      </div>

      {/* Optional Idea Description */}
      <div className="form-group" style={{ marginBottom: '24px' }}>
        <label className="form-label" htmlFor="idea-desc">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <line x1="10" y1="9" x2="8" y2="9"/>
          </svg>
          Describe your idea (optional)
        </label>
        <textarea
          id="idea-desc"
          className="form-control"
          placeholder="Example: I want to build a service for college students..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={isLoading}
          rows={3}
        />
        <span className="form-helper">
          Leave blank to discover all opportunities in this area, or add details to steer the analysis.
        </span>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        className="btn-primary"
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2.5px', margin: 0 }} />
            <span>Analyzing market opportunities...</span>
          </>
        ) : (
          <>
            <span>Find Opportunities</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </>
        )}
      </button>
    </form>
  );
}
