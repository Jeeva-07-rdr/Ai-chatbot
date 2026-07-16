import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';
import { FiUser, FiLock, FiEye, FiEyeOff, FiArrowLeft } from 'react-icons/fi';

const ForgotPassword = () => {
  const [username, setUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const [isVerified, setIsVerified] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const { showToast } = useAuth();
  const navigate = useNavigate();

  const handleVerifyUser = async (e) => {
    e.preventDefault();
    if (!username) return;

    setIsLoading(true);
    try {
      const response = await api.post('/auth/forgot-password', { username });
      showToast(response.data.message || 'User ID verified. Set your new password.', 'success');
      setIsVerified(true);
    } catch (err) {
      const errMsg = err.response?.data?.message || 'User ID verification failed.';
      showToast(errMsg, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!newPassword || !confirmPassword) return;

    if (newPassword !== confirmPassword) {
      showToast('Passwords do not match.', 'error');
      return;
    }

    if (newPassword.length < 6) {
      showToast('Password must be at least 6 characters long.', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.post('/auth/reset-password', { username, newPassword });
      showToast(response.data.message || 'Password reset successful!', 'success');
      navigate('/login');
    } catch (err) {
      const errMsg = err.response?.data?.message || 'Failed to reset password.';
      showToast(errMsg, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
          <Link to="/login" style={{ display: 'flex', alignItems: 'center', color: 'var(--text-secondary)', textDecoration: 'none', gap: '6px', fontSize: '14px' }}>
            <FiArrowLeft /> Back to Login
          </Link>
        </div>

        <div className="auth-header">
          <div className="auth-logo">?</div>
          <h2 className="auth-title">Reset Password</h2>
          <p className="auth-subtitle">
            {!isVerified 
              ? 'Enter User ID associated with your administrator account' 
              : 'Enter details to update password in database'}
          </p>
        </div>

        {!isVerified ? (
          <form onSubmit={handleVerifyUser}>
            <div className="form-group">
              <label className="form-label">User ID</label>
              <div className="input-wrapper">
                <span className="input-icon"><FiUser /></span>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Enter User ID (e.g. admin)"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            <button type="submit" className="btn" disabled={isLoading}>
              {isLoading ? 'Verifying...' : 'Verify User ID'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleResetPassword}>
            <div className="form-group">
              <label className="form-label">Verified User ID</label>
              <div className="input-wrapper">
                <span className="input-icon"><FiUser /></span>
                <input
                  type="text"
                  className="form-control"
                  value={username}
                  disabled
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">New Password</label>
              <div className="input-wrapper">
                <span className="input-icon"><FiLock /></span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="form-control"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Confirm New Password</label>
              <div className="input-wrapper">
                <span className="input-icon"><FiLock /></span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="form-control"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button type="submit" className="btn" disabled={isLoading}>
              {isLoading ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;
