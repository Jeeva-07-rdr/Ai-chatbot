import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../utils/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Custom Toast State
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  useEffect(() => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');

    if (token && storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (username, password, rememberMe) => {
    try {
      const response = await api.post('/auth/login', { username, password });
      const { token, user } = response.data;
      
      const storage = rememberMe ? localStorage : sessionStorage;
      storage.setItem('token', token);
      storage.setItem('user', JSON.stringify(user));
      
      setUser(user);
      showToast('Login successful!', 'success');
      return true;
    } catch (error) {
      const errMsg = error.response?.data?.message || 'Login failed. Please check credentials.';
      showToast(errMsg, 'error');
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
    setUser(null);
    showToast('Logged out successfully', 'success');
  };

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => {
      setToast((prev) => ({ ...prev, show: false }));
    }, 3000);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, showToast }}>
      {children}
      
      {/* Dynamic Toast Element */}
      <div className={`toast-box ${toast.type} ${toast.show ? 'show' : ''}`}>
        <span className={`toast-icon ${toast.type}`}>
          {toast.type === 'success' && '✓'}
          {toast.type === 'error' && '✗'}
          {toast.type === 'warning' && '⚠'}
        </span>
        <span className="toast-msg">{toast.message}</span>
      </div>
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
export default AuthContext;
