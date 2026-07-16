import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import EmployeeModal from '../components/EmployeeModal';
import EmployeeDetailModal from '../components/EmployeeDetailModal';
import ConfirmDialog from '../components/ConfirmDialog';

import { 
  FiSearch, FiPlus, FiRefreshCw, FiEye, FiEdit2, FiTrash2, 
  FiToggleRight, FiUsers, FiLayers, FiDollarSign, FiActivity, 
  FiArrowUp, FiArrowDown, FiFilter, FiUserX, FiCalendar, 
  FiCheckCircle, FiClock, FiFileText
} from 'react-icons/fi';

const Dashboard = () => {
  const { showToast } = useAuth();
  const location = useLocation();
  const isDashboardPath = location.pathname === '/';
  
  // Base raw data from backend
  const [rawEmployees, setRawEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Advanced Frontend Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('Active'); // Backend query status: Active, Inactive, All
  const [deptFilter, setDeptFilter] = useState('All');
  const [salaryFilter, setSalaryFilter] = useState('All'); // All, <3L, 3L-6L, 6L-12L, >12L
  const [sortBy, setSortBy] = useState('created_at');
  const [order, setOrder] = useState('DESC');
  
  // Frontend Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);

  // Stats Card state
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    inactive: 0,
    departments: 0,
    payroll: 0
  });

  // Modal states
  const [isEmployeeModalOpen, setIsEmployeeModalOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [detailEmployee, setDetailEmployee] = useState(null);
  
  // Confirm Dialog state
  const [confirmState, setConfirmState] = useState({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
    isDanger: false
  });

  // Fetch employees list from backend (large limit so we can perform client-side filtering)
  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await api.get('/employees', {
        params: {
          status: statusFilter, // Send status filter to backend
          search: '',           // Empty so we fetch full set and do premium live filters
          limit: 10000          // High limit to pull database set
        }
      });
      setRawEmployees(response.data.employees);
    } catch (error) {
      showToast('Error loading directory from MySQL server', 'error');
    } finally {
      // Small artificial timeout to demonstrate skeleton loader smoothly
      setTimeout(() => {
        setLoading(false);
      }, 500);
    }
  };

  // Calculate dynamic stats
  const calculateStats = () => {
    if (!rawEmployees) return;
    
    const total = rawEmployees.length;
    const active = rawEmployees.filter(e => e.status === 'Active').length;
    const inactive = total - active;
    
    // Unique departments count
    const depts = new Set(rawEmployees.map(e => e.department));
    
    // Payroll (Monthly Payroll)
    const annualPayroll = rawEmployees
      .filter(e => e.status === 'Active')
      .reduce((acc, curr) => acc + parseFloat(curr.salary || 0), 0);
    const monthlyPayroll = annualPayroll / 12;

    setStats({
      total,
      active,
      inactive,
      departments: depts.size || 5,
      payroll: monthlyPayroll
    });
  };

  useEffect(() => {
    fetchEmployees();
  }, [statusFilter]);

  useEffect(() => {
    calculateStats();
    setCurrentPage(1); // Reset page on data load
  }, [rawEmployees]);

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setCurrentPage(1);
  };

  const handleRefresh = () => {
    setSearch('');
    setDeptFilter('All');
    setSalaryFilter('All');
    setStatusFilter('Active');
    setSortBy('created_at');
    setOrder('DESC');
    setCurrentPage(1);
    fetchEmployees();
    showToast('Directory records synchronized with MySQL', 'success');
  };

  // Reset all filters specifically
  const handleResetFilters = () => {
    setSearch('');
    setDeptFilter('All');
    setSalaryFilter('All');
    setCurrentPage(1);
    showToast('Advanced filters reset to default', 'success');
  };

  // Sorting handler
  const handleSort = (column) => {
    if (sortBy === column) {
      setOrder(order === 'ASC' ? 'DESC' : 'ASC');
    } else {
      setSortBy(column);
      setOrder('ASC');
    }
    setCurrentPage(1);
  };

  // Apply filters and sorting on client side
  const getProcessedEmployees = () => {
    let filtered = [...rawEmployees];

    // 1. Text Search (ID, Name, Department, Designation, Email, Phone)
    if (search.trim() !== '') {
      const q = search.toLowerCase().trim();
      filtered = filtered.filter(emp => 
        (emp.employee_id && emp.employee_id.toLowerCase().includes(q)) ||
        (emp.employee_name && emp.employee_name.toLowerCase().includes(q)) ||
        (emp.department && emp.department.toLowerCase().includes(q)) ||
        (emp.designation && emp.designation.toLowerCase().includes(q)) ||
        (emp.email && emp.email.toLowerCase().includes(q)) ||
        (emp.phone && emp.phone.includes(q))
      );
    }

    // 2. Department Filter
    if (deptFilter !== 'All') {
      filtered = filtered.filter(emp => emp.department === deptFilter);
    }

    // 3. Salary Range Filter (INR)
    if (salaryFilter !== 'All') {
      filtered = filtered.filter(emp => {
        const sal = parseFloat(emp.salary || 0);
        if (salaryFilter === 'under3') return sal < 300000;
        if (salaryFilter === '3to6') return sal >= 300000 && sal <= 600000;
        if (salaryFilter === '6to12') return sal >= 600000 && sal <= 1200000;
        if (salaryFilter === 'over12') return sal > 1200000;
        return true;
      });
    }

    // 4. Sorting
    filtered.sort((a, b) => {
      let valA = a[sortBy];
      let valB = b[sortBy];

      // Convert salary/age to numbers if sorting
      if (sortBy === 'salary') {
        valA = parseFloat(valA || 0);
        valB = parseFloat(valB || 0);
      } else if (sortBy === 'age') {
        valA = parseInt(valA || 0);
        valB = parseInt(valB || 0);
      } else {
        // Safe string comparisons
        valA = valA ? String(valA).toLowerCase() : '';
        valB = valB ? String(valB).toLowerCase() : '';
      }

      if (valA < valB) return order === 'ASC' ? -1 : 1;
      if (valA > valB) return order === 'ASC' ? 1 : -1;
      return 0;
    });

    return filtered;
  };

  const processedEmployees = getProcessedEmployees();

  // Paginated records calculation
  const totalItems = processedEmployees.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedEmployees = processedEmployees.slice(startIndex, startIndex + itemsPerPage);

  // Add/Edit Save callback
  const handleSaveEmployee = async (employeeData) => {
    try {
      if (selectedEmployee) {
        await api.put(`/employees/${selectedEmployee.id}`, employeeData);
        showToast('Employee details updated successfully', 'success');
      } else {
        await api.post('/employees', employeeData);
        showToast('Employee registered successfully in database', 'success');
      }
      setIsEmployeeModalOpen(false);
      setSelectedEmployee(null);
      fetchEmployees();
    } catch (error) {
      const errMsg = error.response?.data?.message || 'Failed to save employee records.';
      showToast(errMsg, 'error');
    }
  };

  // Soft delete callback
  const handleDeleteEmployee = (emp) => {
    setConfirmState({
      isOpen: true,
      title: 'Deactivate & Soft Delete',
      message: `Confirm soft delete for ${emp.employee_name}? The status will change to Inactive and remain in MySQL.`,
      isDanger: true,
      onConfirm: async () => {
        try {
          await api.delete(`/employees/${emp.id}`);
          showToast('Employee record soft-deleted', 'success');
          fetchEmployees();
        } catch (error) {
          showToast('Failed to soft delete employee', 'error');
        }
        closeConfirm();
      }
    });
  };

  // Quick Status Toggle
  const handleStatusToggle = (emp) => {
    const newStatus = emp.status === 'Active' ? 'Inactive' : 'Active';
    
    setConfirmState({
      isOpen: true,
      title: 'Toggle Employment Status',
      message: `Change ${emp.employee_name}'s status to ${newStatus}?`,
      isDanger: newStatus === 'Inactive',
      onConfirm: async () => {
        try {
          await api.put(`/employees/${emp.id}/status`, { status: newStatus });
          showToast(`Status changed to ${newStatus}`, 'success');
          
          if (isDetailModalOpen && detailEmployee && detailEmployee.id === emp.id) {
            setDetailEmployee({ ...detailEmployee, status: newStatus });
          }
          
          fetchEmployees();
        } catch (error) {
          showToast('Failed to toggle status', 'error');
        }
        closeConfirm();
      }
    });
  };

  const closeConfirm = () => {
    setConfirmState({
      isOpen: false,
      title: '',
      message: '',
      onConfirm: () => {},
      isDanger: false
    });
  };

  const openAddModal = () => {
    setSelectedEmployee(null);
    setIsEmployeeModalOpen(true);
  };

  const openEditModal = (emp) => {
    setSelectedEmployee(emp);
    setIsEmployeeModalOpen(true);
  };

  const openDetailModal = (emp) => {
    setDetailEmployee(emp);
    setIsDetailModalOpen(true);
  };

  const renderSortIndicator = (column) => {
    if (sortBy !== column) return null;
    return order === 'ASC' ? <FiArrowUp className="sort-icon" /> : <FiArrowDown className="sort-icon" />;
  };

  // Helper to color avatar tags
  const getAvatarColorClass = (dept) => {
    if (dept === 'Engineering') return '#5B5FEF';
    if (dept === 'Human Resources') return '#16C784';
    if (dept === 'Marketing') return '#F5A623';
    if (dept === 'Finance') return '#7C6CFF';
    return '#FF4D4F'; // Sales / others
  };

  return (
    <div className="dashboard-layout">
      {/* Collapsible Sidebar */}
      <Sidebar />

      <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
        {/* Navbar Header */}
        <Header 
          pageTitle={isDashboardPath ? "Dashboard Overview" : "Staff Directory"} 
          pageSubtitle={isDashboardPath ? "Enterprise Analytics and Management Console" : "Real-time Personnel Registry"} 
        />

        {/* Page Contents */}
        <div className="page-content">
          
          {isDashboardPath ? (
            /* Route: '/' -> General Dashboard Analytics */
            <>
              {/* SaaS Statistics Grid */}
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-card-header">
                    <div className="stat-icon indigo"><FiUsers /></div>
                    <span className="stat-trend neutral">Staff</span>
                  </div>
                  <div className="stat-card-body">
                    <span className="stat-value">{stats.total}</span>
                    <span className="stat-label">Total Registered</span>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-card-header">
                    <div className="stat-icon green"><FiCheckCircle /></div>
                    <span className="stat-trend up">+100%</span>
                  </div>
                  <div className="stat-card-body">
                    <span className="stat-value">{stats.active}</span>
                    <span className="stat-label">Active Directory</span>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-card-header">
                    <div className="stat-icon danger"><FiUserX /></div>
                    <span className="stat-trend neutral">Muted</span>
                  </div>
                  <div className="stat-card-body">
                    <span className="stat-value">{stats.inactive}</span>
                    <span className="stat-label">Inactive Accounts</span>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-card-header">
                    <div className="stat-icon purple"><FiLayers /></div>
                    <span className="stat-trend neutral">Biz Units</span>
                  </div>
                  <div className="stat-card-body">
                    <span className="stat-value">{stats.departments}</span>
                    <span className="stat-label">Active Departments</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-card-header">
                    <div className="stat-icon warning"><FiDollarSign /></div>
                    <span className="stat-trend up">INR (₹)</span>
                  </div>
                  <div className="stat-card-body">
                    <span className="stat-value">
                      {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(stats.payroll)}
                    </span>
                    <span className="stat-label">Est. Monthly Payroll</span>
                  </div>
                </div>
              </div>

              {/* Welcome Action Banner */}
              <div className="stat-card" style={{ padding: '28px', background: 'radial-gradient(circle at 100% 100%, rgba(91, 95, 239, 0.08) 0%, transparent 60%), var(--bg-card)' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px', color: 'var(--text-primary)' }}>
                  Welcome back to your EMS Workspace!
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.6', maxWidth: '640px', marginBottom: '16px' }}>
                  The directory currently has <strong>{stats.active} active</strong> staff profiles across <strong>{stats.departments} active business units</strong>. You can navigate to the employee directory database to add new hires, edit personal detail fields, toggle profile statuses, or perform soft deletions.
                </p>
                <Link to="/employees" className="btn" style={{ width: 'auto', display: 'inline-flex', padding: '10px 20px', textDecoration: 'none' }}>
                  Manage Employee Directory &rarr;
                </Link>
              </div>

              {/* Recently Added summary list */}
              <div className="module-container">
                <div className="module-header" style={{ padding: '16px 20px' }}>
                  <h3 className="module-title">Recently Registered Personnel</h3>
                </div>
                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Designation</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rawEmployees.slice(0, 5).map((emp) => (
                        <tr key={emp.id}>
                          <td style={{ fontWeight: '600', fontFamily: 'monospace' }}>{emp.employee_id}</td>
                          <td>{emp.employee_name}</td>
                          <td><span className="dept-badge">{emp.department}</span></td>
                          <td>{emp.designation}</td>
                          <td>
                            <span className={`badge ${emp.status === 'Active' ? 'badge-active' : 'badge-inactive'}`}>
                              {emp.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                      {rawEmployees.length === 0 && (
                        <tr>
                          <td colSpan="5" style={{ textStyle: 'italic', textAlign: 'center', padding: '20px', color: 'var(--text-secondary)' }}>
                            No employee records exist in the database.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            /* Route: '/employees' -> Personnel Table and Filters */
            <div className="module-container">
              
              {/* Header controls toolbar */}
              <div className="module-header">
                <div className="module-title-row">
                  <h3 className="module-title">Personnel Roster ({totalItems} records)</h3>
                  
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn-icon" onClick={handleRefresh} title="Sync database data">
                      <FiRefreshCw />
                    </button>
                    <button className="btn" onClick={openAddModal} style={{ width: 'auto', padding: '8px 14px' }}>
                      <FiPlus />
                      <span>Add Employee</span>
                    </button>
                  </div>
                </div>
                
                {/* Advanced Filters Panel */}
                <div className="module-controls">
                  
                  {/* 1. Live search query */}
                  <div className="search-input-wrapper">
                    <FiSearch className="search-icon" />
                    <input
                      type="text"
                      className="search-field"
                      placeholder="Search name, ID, designation..."
                      value={search}
                      onChange={handleSearchChange}
                    />
                    {search && (
                      <button 
                        onClick={() => { setSearch(''); setCurrentPage(1); }} 
                        style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '16px' }}
                      >
                        &times;
                      </button>
                    )}
                  </div>

                  {/* 2. Status backend query selector */}
                  <select
                    className="select-field"
                    value={statusFilter}
                    onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
                  >
                    <option value="Active">Status: Active Only</option>
                    <option value="Inactive">Status: Inactive Only</option>
                    <option value="All">Status: All Records</option>
                  </select>

                  {/* 3. Department filter */}
                  <select
                    className="select-field"
                    value={deptFilter}
                    onChange={(e) => { setDeptFilter(e.target.value); setCurrentPage(1); }}
                  >
                    <option value="All">Dept: All Units</option>
                    <option value="Human Resources">Human Resources</option>
                    <option value="Engineering">Engineering</option>
                    <option value="Marketing">Marketing</option>
                    <option value="Sales">Sales</option>
                    <option value="Finance">Finance</option>
                  </select>

                  {/* 4. Salary filter */}
                  <select
                    className="select-field"
                    value={salaryFilter}
                    onChange={(e) => { setSalaryFilter(e.target.value); setCurrentPage(1); }}
                  >
                    <option value="All">Salary: Any Range</option>
                    <option value="under3">Salary: Under ₹3 Lakhs</option>
                    <option value="3to6">Salary: ₹3L - ₹6 Lakhs</option>
                    <option value="6to12">Salary: ₹6L - ₹12 Lakhs</option>
                    <option value="over12">Salary: Over ₹12 Lakhs</option>
                  </select>

                  {/* 5. Reset button */}
                  {(search || deptFilter !== 'All' || salaryFilter !== 'All') && (
                    <button 
                      className="btn btn-secondary" 
                      onClick={handleResetFilters}
                      style={{ width: 'auto', padding: '8px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      <FiFilter />
                      Reset
                    </button>
                  )}

                </div>
              </div>

              {/* Table layout with skeleton support */}
              <div className="table-responsive">
                {loading ? (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Designation</th>
                        <th>Salary</th>
                        <th>Phone</th>
                        <th>Email</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Array.from({ length: itemsPerPage }).map((_, idx) => (
                        <tr key={idx} className="skeleton-row">
                          <td><div className="skeleton-text short"></div></td>
                          <td><div className="skeleton-text"></div></td>
                          <td><div className="skeleton-text short"></div></td>
                          <td><div className="skeleton-text"></div></td>
                          <td><div className="skeleton-text short"></div></td>
                          <td><div className="skeleton-text"></div></td>
                          <td><div className="skeleton-text long"></div></td>
                          <td><div className="skeleton-text short"></div></td>
                          <td><div className="skeleton-text short"></div></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : totalItems === 0 ? (
                  // Clean SVG Empty State Illustration
                  <div className="empty-state-container">
                    <svg className="empty-state-svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 13h6m-3-3v6m-9 1V4a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                    </svg>
                    <h4 className="empty-state-title">No employees found</h4>
                    <p className="empty-state-desc">
                      We couldn't find any staff profiles matching your current search queries or filters. Try resetting the filters or add a new employee profile.
                    </p>
                    <button 
                      className="btn" 
                      onClick={openAddModal}
                      style={{ width: 'auto', padding: '8px 16px', marginTop: '8px' }}
                    >
                      <FiPlus />
                      <span>Register Employee</span>
                    </button>
                  </div>
                ) : (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th onClick={() => handleSort('employee_id')}>ID {renderSortIndicator('employee_id')}</th>
                        <th onClick={() => handleSort('employee_name')}>Name {renderSortIndicator('employee_name')}</th>
                        <th onClick={() => handleSort('department')}>Department {renderSortIndicator('department')}</th>
                        <th onClick={() => handleSort('designation')}>Designation {renderSortIndicator('designation')}</th>
                        <th onClick={() => handleSort('salary')}>Salary {renderSortIndicator('salary')}</th>
                        <th onClick={() => handleSort('phone')}>Phone {renderSortIndicator('phone')}</th>
                        <th onClick={() => handleSort('email')}>Email {renderSortIndicator('email')}</th>
                        <th onClick={() => handleSort('status')}>Status {renderSortIndicator('status')}</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedEmployees.map((emp) => {
                        const isActive = emp.status === 'Active';
                        return (
                          <tr key={emp.id}>
                            <td style={{ fontWeight: '600', color: 'var(--text-primary)', fontFamily: 'monospace' }}>{emp.employee_id}</td>
                            <td>
                              <div className="table-avatar-cell">
                                <div 
                                  className="table-avatar"
                                  style={{ backgroundColor: getAvatarColorClass(emp.department) }}
                                >
                                  {emp.employee_name.charAt(0).toUpperCase()}
                                </div>
                                {emp.employee_name}
                              </div>
                            </td>
                            <td>
                              <span className="dept-badge">{emp.department}</span>
                            </td>
                            <td>{emp.designation}</td>
                            <td style={{ fontWeight: '500', color: 'var(--text-primary)' }}>
                              {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(emp.salary)}
                            </td>
                            <td>{emp.phone}</td>
                            <td>{emp.email}</td>
                            <td>
                              <span 
                                className={`badge ${isActive ? 'badge-active' : 'badge-inactive'}`}
                                onClick={() => handleStatusToggle(emp)}
                                title="Click to toggle status quickly"
                              >
                                {emp.status}
                              </span>
                            </td>
                            <td>
                              <div className="action-buttons">
                                <button className="btn-action view" title="View Profile" onClick={() => openDetailModal(emp)}>
                                  <FiEye />
                                </button>
                                
                                <button className="btn-action edit" title="Edit Records" onClick={() => openEditModal(emp)}>
                                  <FiEdit2 />
                                </button>
                                
                                {isActive ? (
                                  <button className="btn-action delete" title="Deactivate" onClick={() => handleDeleteEmployee(emp)}>
                                    <FiTrash2 />
                                  </button>
                                ) : (
                                  <button className="btn-action toggle-active" title="Activate Employee" onClick={() => handleStatusToggle(emp)}>
                                    <FiToggleRight />
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Pagination Controls */}
              {totalItems > 0 && (
                <div className="pagination-container">
                  <div className="pagination-info">
                    Showing <b>{startIndex + 1}</b> to <b>{Math.min(startIndex + itemsPerPage, totalItems)}</b> of <b>{totalItems}</b> employees
                  </div>

                  <div className="pagination-controls">
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)', marginRight: '8px' }}>Rows per page:</span>
                    <select
                      className="select-field"
                      value={itemsPerPage}
                      onChange={(e) => { setItemsPerPage(parseInt(e.target.value)); setCurrentPage(1); }}
                      style={{ padding: '4px 8px', fontSize: '13px', minWidth: '60px', marginRight: '16px', width: 'auto' }}
                    >
                      <option value="5">5</option>
                      <option value="10">10</option>
                      <option value="20">20</option>
                      <option value="50">50</option>
                    </select>

                    <button 
                      className="btn-page" 
                      disabled={currentPage === 1} 
                      onClick={() => setCurrentPage(currentPage - 1)}
                    >
                      ‹
                    </button>
                    
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((pNum) => (
                      <button
                        key={pNum}
                        className={`btn-page ${currentPage === pNum ? 'active' : ''}`}
                        onClick={() => setCurrentPage(pNum)}
                      >
                        {pNum}
                      </button>
                    ))}

                    <button 
                      className="btn-page" 
                      disabled={currentPage === totalPages} 
                      onClick={() => setCurrentPage(currentPage + 1)}
                    >
                      ›
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

        </div>
      </div>

      {/* Popups & Modals */}
      <EmployeeModal 
        isOpen={isEmployeeModalOpen}
        employee={selectedEmployee}
        onClose={() => { setIsEmployeeModalOpen(false); setSelectedEmployee(null); }}
        onSave={handleSaveEmployee}
      />

      <EmployeeDetailModal
        isOpen={isDetailModalOpen}
        employee={detailEmployee}
        onClose={() => { setIsDetailModalOpen(false); setDetailEmployee(null); }}
        onToggleStatus={handleStatusToggle}
      />

      <ConfirmDialog
        isOpen={confirmState.isOpen}
        title={confirmState.title}
        message={confirmState.message}
        isDanger={confirmState.isDanger}
        onConfirm={confirmState.onConfirm}
        onCancel={closeConfirm}
      />
    </div>
  );
};

export default Dashboard;
