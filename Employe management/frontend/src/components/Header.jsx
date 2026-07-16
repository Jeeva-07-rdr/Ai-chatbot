import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { FiClock, FiBell, FiSun, FiMoon, FiChevronDown, FiUser, FiLogOut } from 'react-icons/fi';

const Header = ({ pageTitle = 'Dashboard', pageSubtitle = 'Welcome back to Enterprise EMS' }) => {
  const { user, logout } = useAuth();
  const [timeString, setTimeString] = useState('');
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return localStorage.getItem('theme') !== 'light';
  });

  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.remove('light-theme');
    } else {
      document.body.classList.add('light-theme');
    }
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  const dropdownRef = useRef(null);

  useEffect(() => {
    const updateTime = () => {
      const options = {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      };
      setTimeString(new Date().toLocaleDateString('en-US', options));
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsProfileMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getInitials = (username) => {
    if (!username) return 'A';
    return username.charAt(0).toUpperCase();
  };

  return (
    <header className="header">
      {/* Breadcrumb and Page title */}
      <div className="header-title-section">
        <div className="header-breadcrumb">
          <span>Portal</span>
          <span className="header-breadcrumb-sep">/</span>
          <span style={{ color: 'var(--text-primary)' }}>{pageTitle}</span>
        </div>
        <h1 className="header-title">{pageSubtitle}</h1>
      </div>

      <div className="header-right-panel">
        {/* Realtime clock */}
        <div className="header-time-widget">
          <FiClock />
          <span>{timeString}</span>
        </div>

        <div className="header-actions">
          {/* Light/Dark mode mock toggle */}
          <button 
            className="header-btn" 
            onClick={() => setIsDarkMode(!isDarkMode)}
            title="Toggle Light/Dark Theme (Visual)"
          >
            {isDarkMode ? <FiSun /> : <FiMoon />}
          </button>

          {/* Notifications bell */}
          <div style={{ position: 'relative' }}>
            <button className="header-btn" title="Notifications">
              <FiBell />
              {/* Alert indicator dot */}
              <span style={{
                position: 'absolute',
                top: '6px',
                right: '6px',
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: 'var(--danger-color)',
                border: '2px solid var(--bg-primary)'
              }}></span>
            </button>
          </div>
        </div>

        {/* User profile with dropdown menu */}
        <div style={{ position: 'relative' }} ref={dropdownRef}>
          <div 
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px', 
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: '8px',
              transition: 'background-color 0.2s'
            }}
            onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
            className="header-user-badge"
          >
            <div className="header-avatar">
              {getInitials(user?.username)}
            </div>
            <FiChevronDown style={{ color: 'var(--text-secondary)', fontSize: '14px' }} />
          </div>

          {/* Profile Dropdown panel */}
          {isProfileMenuOpen && (
            <div style={{
              position: 'absolute',
              top: '110%',
              right: 0,
              width: '200px',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              boxShadow: 'var(--shadow-lg)',
              padding: '6px',
              display: 'flex',
              flexDirection: 'column',
              zIndex: 200
            }}>
              <div style={{
                padding: '10px 12px',
                borderBottom: '1px solid var(--border-color)',
                display: 'flex',
                flexDirection: 'column',
                gap: '2px'
              }}>
                <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
                  {user?.username || 'Administrator'}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  {user?.email || 'admin@enterprise.com'}
                </span>
              </div>

              <div style={{ padding: '4px 0' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 12px',
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  borderRadius: '6px'
                }} className="dropdown-item-hover">
                  <FiUser />
                  <span>My Profile</span>
                </div>

                <div 
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '8px 12px',
                    fontSize: '13px',
                    color: 'var(--danger-color)',
                    cursor: 'pointer',
                    borderRadius: '6px'
                  }}
                  className="dropdown-item-hover"
                  onClick={logout}
                >
                  <FiLogOut />
                  <span>Sign Out</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
