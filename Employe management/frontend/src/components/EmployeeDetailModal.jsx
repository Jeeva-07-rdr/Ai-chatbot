import React from 'react';
import { FiX, FiCheckCircle, FiXCircle, FiPrinter, FiMail, FiPhone, FiMapPin, FiCalendar, FiDollarSign } from 'react-icons/fi';

const EmployeeDetailModal = ({ isOpen, employee, onClose, onToggleStatus }) => {
  if (!isOpen || !employee) return null;

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatSalary = (val) => {
    if (val === undefined || val === null) return 'N/A';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  const isActive = employee.status === 'Active';

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '600px' }}>
        <div className="modal-header">
          <h3 className="modal-title">Employee Profile Card</h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn-close" onClick={handlePrint} title="Print Profile Sheet" style={{ marginRight: '8px' }}>
              <FiPrinter />
            </button>
            <button className="btn-close" onClick={onClose}><FiX /></button>
          </div>
        </div>

        <div className="modal-body" id="print-section">
          {/* Header Panel with large avatar card */}
          <div className="detail-header-panel">
            <div className="detail-avatar-large">
              {employee.employee_name.charAt(0).toUpperCase()}
            </div>
            
            <div className="detail-name-row">
              <h2 style={{ fontSize: '18px', fontWeight: '600', color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>
                {employee.employee_name}
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '2px' }}>
                {employee.designation} • <span style={{ color: 'var(--accent-color)', fontWeight: '500' }}>{employee.department}</span>
              </p>
            </div>

            <div>
              <span className={`badge ${isActive ? 'badge-active' : 'badge-inactive'}`}>
                {employee.status}
              </span>
            </div>
          </div>

          {/* Details list structured inside rounded grids */}
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">Employee ID</span>
              <span className="detail-value" style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>{employee.employee_id}</span>
            </div>

            <div className="detail-item">
              <span className="detail-label">Gender</span>
              <span className="detail-value">{employee.gender}</span>
            </div>

            <div className="detail-item">
              <span className="detail-label">
                <FiMail style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                Email Address
              </span>
              <span className="detail-value" style={{ wordBreak: 'break-all', fontSize: '12px' }}>{employee.email}</span>
            </div>

            <div className="detail-item">
              <span className="detail-label">
                <FiPhone style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                Phone Number
              </span>
              <span className="detail-value">{employee.phone}</span>
            </div>

            <div className="detail-item">
              <span className="detail-label">
                <FiCalendar style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                Date of Birth
              </span>
              <span className="detail-value">{formatDate(employee.dob)} ({employee.age} years)</span>
            </div>

            <div className="detail-item">
              <span className="detail-label">
                <FiCalendar style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                Date of Joining
              </span>
              <span className="detail-value">{formatDate(employee.joining_date)}</span>
            </div>

            <div className="detail-item">
              <span className="detail-label">
                <FiDollarSign style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                Current Salary
              </span>
              <span className="detail-value" style={{ color: 'var(--success-color)', fontWeight: '600' }}>
                {formatSalary(employee.salary)} / year
              </span>
            </div>

            <div className="detail-item">
              <span className="detail-label">Record Created</span>
              <span className="detail-value">{formatDate(employee.created_at)}</span>
            </div>

            <div className="detail-item col-span-2">
              <span className="detail-label">
                <FiMapPin style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                Home Address
              </span>
              <span className="detail-value address" style={{ fontSize: '12px' }}>{employee.address}</span>
            </div>
          </div>
        </div>

        <div className="modal-footer" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <button 
              type="button" 
              className={`btn ${isActive ? 'btn-outline-danger' : 'btn'}`} 
              onClick={() => onToggleStatus(employee)}
              style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 14px', fontSize: '13px' }}
            >
              {isActive ? (
                <>
                  <FiXCircle />
                  Deactivate Account
                </>
              ) : (
                <>
                  <FiCheckCircle />
                  Activate Account
                </>
              )}
            </button>
          </div>
          
          <div>
            <button className="btn btn-secondary" onClick={onClose} style={{ width: 'auto', padding: '8px 16px' }}>
              Close Card
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmployeeDetailModal;
