import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  FiHome, FiUsers, FiLayers, FiCalendar, FiDollarSign, 
  FiTrendingUp, FiSettings, FiLogOut, FiChevronLeft, FiChevronRight 
} from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { user, logout } = useAuth();
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem('sidebar-collapsed') === 'true';
  });

  useEffect(() => {
    const layout = document.querySelector('.dashboard-layout');
    if (layout) {
      if (isCollapsed) {
        layout.classList.add('sidebar-collapsed');
      } else {
        layout.classList.remove('sidebar-collapsed');
      }
    }
    localStorage.setItem('sidebar-collapsed', isCollapsed);
  }, [isCollapsed]);

  const menuItems = [
    { name: 'Dashboard', icon: <FiHome />, path: '/' },
    { name: 'Employees', icon: <FiUsers />, path: '/employees' }
  ];

  const getInitials = (username) => {
    if (!username) return 'A';
    return username.charAt(0).toUpperCase();
  };

  return (
    <div className="sidebar">
      {/* Sidebar Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo">Ω</div>
        <span className="sidebar-brand">Enterprise EMS</span>
        <button 
          className="sidebar-toggle-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isCollapsed ? <FiChevronRight /> : <FiChevronLeft />}
        </button>
      </div>

      {/* Navigation menu items */}
      <nav className="sidebar-menu">
        {menuItems.map((item, idx) => {
          if (item.disabled) {
            return (
              <div key={idx} className="sidebar-item-link disabled" title={`${item.name} (Future feature)`}>
                {item.icon}
                <span>{item.name}</span>
              </div>
            );
          }
          return (
            <NavLink
              key={idx}
              to={item.path}
              className={({ isActive }) => `sidebar-item-link ${isActive ? 'active' : ''}`}
            >
              {item.icon}
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* User Profile bottom Panel */}
      <div className="sidebar-footer">
        <div className="sidebar-user-card" title={`Logged in as ${user?.username || 'Administrator'}`}>
          <div className="sidebar-user-avatar">
            {getInitials(user?.username)}
          </div>
          <div className="sidebar-user-info">
            <span className="sidebar-user-name">{user?.username || 'Admin'}</span>
            <span className="sidebar-user-role">{user?.role || 'Admin'}</span>
          </div>
          <button 
            onClick={logout} 
            style={{ 
              marginLeft: 'auto', 
              background: 'none', 
              border: 'none', 
              color: 'var(--text-muted)', 
              cursor: 'pointer',
              display: isCollapsed ? 'none' : 'flex',
              alignItems: 'center',
              fontSize: '15px'
            }}
            title="Log Out"
          >
            <FiLogOut />
          </button>
        </div>
        <span className="sidebar-version">v1.2.0</span>
      </div>
    </div>
  );
};

export default Sidebar;
