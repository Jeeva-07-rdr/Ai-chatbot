import React, { useState, useEffect } from 'react';
import { FiX, FiUser, FiBriefcase, FiPhoneCall, FiSettings } from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';

const EmployeeModal = ({ isOpen, employee = null, onSave, onClose }) => {
  const { showToast } = useAuth();
  const [activeTab, setActiveTab] = useState('personal'); // personal, employment, contact, status
  
  const initialFormState = {
    employee_id: '',
    employee_name: '',
    gender: 'Male',
    dob: '',
    age: '',
    department: 'Engineering',
    designation: '',
    joining_date: '',
    salary: '',
    phone: '',
    email: '',
    address: '',
    status: 'Active'
  };

  const [formData, setFormData] = useState(initialFormState);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (employee) {
      setFormData({
        ...employee,
        dob: employee.dob ? employee.dob.split('T')[0] : '',
        joining_date: employee.joining_date ? employee.joining_date.split('T')[0] : '',
        salary: String(employee.salary)
      });
    } else {
      setFormData(initialFormState);
    }
    setErrors({});
    setActiveTab('personal');
  }, [employee, isOpen]);

  const handleDOBChange = (e) => {
    const dobValue = e.target.value;
    let computedAge = '';
    
    if (dobValue) {
      const birthDate = new Date(dobValue);
      const difference = Date.now() - birthDate.getTime();
      const ageDate = new Date(difference);
      computedAge = Math.abs(ageDate.getUTCFullYear() - 1970);
    }

    setFormData({
      ...formData,
      dob: dobValue,
      age: computedAge ? String(computedAge) : ''
    });
    
    if (computedAge && computedAge >= 18) {
      setErrors(prev => ({ ...prev, dob: false, age: false }));
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    if (value.trim() !== '') {
      setErrors(prev => ({ ...prev, [name]: false }));
    }
  };

  const handleReset = () => {
    if (employee) {
      setFormData({
        ...employee,
        dob: employee.dob ? employee.dob.split('T')[0] : '',
        joining_date: employee.joining_date ? employee.joining_date.split('T')[0] : '',
        salary: String(employee.salary)
      });
    } else {
      setFormData(initialFormState);
    }
    setErrors({});
    showToast('Form fields reset', 'warning');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const newErrors = {};

    // Validate fields manually
    if (!formData.employee_id.trim()) newErrors.employee_id = true;
    if (!formData.employee_name.trim()) newErrors.employee_name = true;
    if (!formData.dob) newErrors.dob = true;
    if (!formData.age || isNaN(formData.age) || parseInt(formData.age) < 18) newErrors.age = true;
    if (!formData.designation.trim()) newErrors.designation = true;
    if (!formData.joining_date) newErrors.joining_date = true;
    if (!formData.salary || isNaN(formData.salary) || parseFloat(formData.salary) <= 0) newErrors.salary = true;
    
    const phoneRegex = /^[0-9+\-\s()]{8,20}$/;
    if (!formData.phone || !phoneRegex.test(formData.phone)) newErrors.phone = true;
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email || !emailRegex.test(formData.email)) newErrors.email = true;
    
    if (!formData.address.trim()) newErrors.address = true;

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      showToast('Please correct validation errors in the fields', 'error');
      
      // Auto shift tab if error is in another section
      if (newErrors.employee_id || newErrors.employee_name || newErrors.dob || newErrors.age) {
        setActiveTab('personal');
      } else if (newErrors.designation || newErrors.joining_date || newErrors.salary) {
        setActiveTab('employment');
      } else if (newErrors.phone || newErrors.email || newErrors.address) {
        setActiveTab('contact');
      }
      return;
    }

    onSave({
      ...formData,
      age: parseInt(formData.age),
      salary: parseFloat(formData.salary)
    });
  };

  if (!isOpen) return null;

  const isEdit = !!employee;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3 className="modal-title">{isEdit ? 'Edit Employee Records' : 'Register New Employee'}</h3>
          <button type="button" className="btn-close" onClick={onClose}><FiX /></button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Navigation Tabs */}
          <div className="form-tabs">
            <button
              type="button"
              className={`form-tab-btn ${activeTab === 'personal' ? 'active' : ''}`}
              onClick={() => setActiveTab('personal')}
            >
              <FiUser style={{ marginRight: '6px', verticalAlign: 'middle' }} />
              Personal Info
            </button>
            <button
              type="button"
              className={`form-tab-btn ${activeTab === 'employment' ? 'active' : ''}`}
              onClick={() => setActiveTab('employment')}
            >
              <FiBriefcase style={{ marginRight: '6px', verticalAlign: 'middle' }} />
              Employment Info
            </button>
            <button
              type="button"
              className={`form-tab-btn ${activeTab === 'contact' ? 'active' : ''}`}
              onClick={() => setActiveTab('contact')}
            >
              <FiPhoneCall style={{ marginRight: '6px', verticalAlign: 'middle' }} />
              Contact Info
            </button>
            <button
              type="button"
              className={`form-tab-btn ${activeTab === 'status' ? 'active' : ''}`}
              onClick={() => setActiveTab('status')}
            >
              <FiSettings style={{ marginRight: '6px', verticalAlign: 'middle' }} />
              Status
            </button>
          </div>

          <div className="modal-body">
            {/* Tab 1: Personal Details */}
            {activeTab === 'personal' && (
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Employee ID *</label>
                  <input
                    type="text"
                    name="employee_id"
                    className={`modal-form-control ${errors.employee_id ? 'error' : ''}`}
                    placeholder="EMP-1001"
                    value={formData.employee_id}
                    onChange={handleChange}
                    disabled={isEdit}
                  />
                  {errors.employee_id && <span style={{ fontSize: '11px', color: 'var(--danger-color)', marginTop: '4px', display: 'block' }}>ID is required</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Employee Name *</label>
                  <input
                    type="text"
                    name="employee_name"
                    className={`modal-form-control ${errors.employee_name ? 'error' : ''}`}
                    placeholder="John Doe"
                    value={formData.employee_name}
                    onChange={handleChange}
                  />
                  {errors.employee_name && <span style={{ fontSize: '11px', color: 'var(--danger-color)', marginTop: '4px', display: 'block' }}>Name is required</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Gender *</label>
                  <select
                    name="gender"
                    className="modal-form-control"
                    value={formData.gender}
                    onChange={handleChange}
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Date of Birth *</label>
                  <input
                    type="date"
                    name="dob"
                    className={`modal-form-control ${errors.dob ? 'error' : ''}`}
                    value={formData.dob}
                    onChange={handleDOBChange}
                  />
                  {errors.dob && <span style={{ fontSize: '11px', color: 'var(--danger-color)', marginTop: '4px', display: 'block' }}>Valid DOB is required</span>}
                </div>

                <div className="form-group col-span-2">
                  <label className="form-label">Age * (Calculated automatically)</label>
                  <input
                    type="number"
                    name="age"
                    className={`modal-form-control ${errors.age ? 'error' : ''}`}
                    placeholder="Min age is 18"
                    value={formData.age}
                    onChange={handleChange}
                    min="18"
                    max="100"
                  />
                  {errors.age && <span style={{ fontSize: '11px', color: 'var(--danger-color)', marginTop: '4px', display: 'block' }}>Age must be numeric and &ge; 18</span>}
                </div>
              </div>
            )}

            {/* Tab 2: Employment Details */}
            {activeTab === 'employment' && (
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Department *</label>
                  <select
                    name="department"
                    className="modal-form-control"
                    value={formData.department}
                    onChange={handleChange}
                  >
                    <option value="Human Resources">Human Resources</option>
                    <option value="Engineering">Engineering</option>
                    <option value="Marketing">Marketing</option>
                    <option value="Sales">Sales</option>
                    <option value="Finance">Finance</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Designation *</label>
                  <input
                    type="text"
                    name="designation"
                    className={`modal-form-control ${errors.designation ? 'error' : ''}`}
                    placeholder="Senior Developer"
                    value={formData.designation}
                    onChange={handleChange}
                  />
                  {errors.designation && <span style={{ fontSize: '11px', color: 'var(--danger-color)', marginTop: '4px', display: 'block' }}>Designation is required</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Joining Date *</label>
                  <input
                    type="date"
                    name="joining_date"
                    className={`modal-form-control ${errors.joining_date ? 'error' : ''}`}
                    value={formData.joining_date}
                    onChange={handleChange}
                  />
                  {errors.joining_date && <span style={{ fontSize: '11px', color: 'var(--danger-color)', marginTop: '4px', display: 'block' }}>Valid joining date is required</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Salary (INR) *</label>
                  <input
                    type="text"
                    name="salary"
                    className={`modal-form-control ${errors.salary ? 'error' : ''}`}
                    placeholder="500000"
                    value={formData.salary}
                    onChange={handleChange}
                  />
                  {errors.salary && <span style={{ fontSize: '11px', color: 'var(--danger-color)', marginTop: '4px', display: 'block' }}>Positive numeric salary is required</span>}
                </div>
              </div>
            )}

            {/* Tab 3: Contact Details */}
            {activeTab === 'contact' && (
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Phone Number *</label>
                  <input
                    type="tel"
                    name="phone"
                    className={`modal-form-control ${errors.phone ? 'error' : ''}`}
                    placeholder="+91 98765 43210"
                    value={formData.phone}
                    onChange={handleChange}
                  />
                  {errors.phone && <span style={{ fontSize: '11px', color: 'var(--danger-color)', marginTop: '4px', display: 'block' }}>Valid phone number is required</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Email Address *</label>
                  <input
                    type="text"
                    name="email"
                    className={`modal-form-control ${errors.email ? 'error' : ''}`}
                    placeholder="name@enterprise.com"
                    value={formData.email}
                    onChange={handleChange}
                  />
                  {errors.email && <span style={{ fontSize: '11px', color: 'var(--danger-color)', marginTop: '4px', display: 'block' }}>Valid email address is required</span>}
                </div>

                <div className="form-group col-span-2">
                  <label className="form-label">Home Address *</label>
                  <textarea
                    name="address"
                    className={`modal-form-control ${errors.address ? 'error' : ''}`}
                    placeholder="Flat No, Block, City, State, PIN"
                    value={formData.address}
                    onChange={handleChange}
                    style={{ minHeight: '80px', resize: 'vertical' }}
                  />
                  {errors.address && <span style={{ fontSize: '11px', color: 'var(--danger-color)', marginTop: '4px', display: 'block' }}>Home address is required</span>}
                </div>
              </div>
            )}

            {/* Tab 4: Status Settings */}
            {activeTab === 'status' && (
              <div className="form-grid">
                <div className="form-group col-span-2">
                  <label className="form-label">Employment Status *</label>
                  <select
                    name="status"
                    className="modal-form-control"
                    value={formData.status}
                    onChange={handleChange}
                  >
                    <option value="Active">Active (Default)</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '10px', display: 'block', lineHeight: '1.4' }}>
                    Setting an employee status to Inactive will remove them from the default view in the directory. You can toggle this status back to Active at any time.
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={handleReset} style={{ width: 'auto', marginRight: 'auto' }}>
              Reset Fields
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClose} style={{ width: 'auto' }}>
              Cancel
            </button>
            <button type="submit" className="btn" style={{ width: 'auto' }}>
              {isEdit ? 'Save Changes' : 'Register Employee'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EmployeeModal;
