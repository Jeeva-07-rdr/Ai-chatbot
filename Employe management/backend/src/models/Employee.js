const { getPool } = require('../config/db');

class Employee {
  static async checkUnique({ employee_id, email, phone, excludeId = null }) {
    const pool = getPool();
    let query = 'SELECT employee_id, email, phone FROM employees WHERE (employee_id = ? OR email = ? OR phone = ?)';
    const params = [employee_id, email, phone];

    if (excludeId) {
      query += ' AND id != ?';
      params.push(excludeId);
    }

    const [rows] = await pool.query(query, params);
    if (rows.length > 0) {
      const match = rows[0];
      if (match.employee_id === employee_id) return { type: 'employee_id', message: 'Employee ID already exists' };
      if (match.email === email) return { type: 'email', message: 'Email address already exists' };
      if (match.phone === phone) return { type: 'phone', message: 'Phone number already exists' };
    }
    return null;
  }

  static async create(data) {
    const pool = getPool();
    const query = `
      INSERT INTO employees 
      (employee_id, employee_name, gender, dob, age, department, designation, joining_date, salary, phone, email, address, status)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;
    const params = [
      data.employee_id,
      data.employee_name,
      data.gender,
      data.dob,
      data.age,
      data.department,
      data.designation,
      data.joining_date,
      data.salary,
      data.phone,
      data.email,
      data.address,
      data.status || 'Active'
    ];
    const [result] = await pool.query(query, params);
    return result.insertId;
  }

  static async findAll({ status = 'Active', search = '', sortBy = 'created_at', order = 'DESC', page = 1, limit = 10 }) {
    const pool = getPool();
    let whereClauses = [];
    const params = [];

    // 1. Status filter
    if (status === 'Active') {
      whereClauses.push('status = "Active"');
    } else if (status === 'Inactive') {
      whereClauses.push('status = "Inactive"');
    } // If 'All', we don't add status filter

    // 2. Search filter (Employee ID, Name, Department, Email, Phone)
    if (search && search.trim() !== '') {
      const searchPattern = `%${search.trim()}%`;
      whereClauses.push(`(
        employee_id LIKE ? OR 
        employee_name LIKE ? OR 
        department LIKE ? OR 
        email LIKE ? OR 
        phone LIKE ?
      )`);
      params.push(searchPattern, searchPattern, searchPattern, searchPattern, searchPattern);
    }

    const whereSql = whereClauses.length > 0 ? `WHERE ${whereClauses.join(' AND ')}` : '';

    // 3. Sorting (Whitelisting to prevent SQL injection)
    const allowedSortColumns = ['employee_id', 'employee_name', 'department', 'designation', 'salary', 'phone', 'email', 'status', 'created_at'];
    const finalSortBy = allowedSortColumns.includes(sortBy) ? sortBy : 'created_at';
    const finalOrder = order.toUpperCase() === 'ASC' ? 'ASC' : 'DESC';

    // 4. Get Total count for pagination
    const countQuery = `SELECT COUNT(*) as total FROM employees ${whereSql}`;
    const [countRows] = await pool.query(countQuery, params);
    const total = countRows[0].total;

    // 5. Pagination
    const parsedPage = parseInt(page) || 1;
    const parsedLimit = parseInt(limit) || 10;
    const offset = (parsedPage - 1) * parsedLimit;

    // We copy parameters for the main query
    const queryParams = [...params];
    queryParams.push(offset, parsedLimit);

    const query = `
      SELECT * FROM employees 
      ${whereSql} 
      ORDER BY ${finalSortBy} ${finalOrder} 
      LIMIT ?, ?
    `;

    const [rows] = await pool.query(query, queryParams);

    return {
      employees: rows,
      pagination: {
        total,
        page: parsedPage,
        limit: parsedLimit,
        totalPages: Math.ceil(total / parsedLimit)
      }
    };
  }

  static async findById(id) {
    const pool = getPool();
    const [rows] = await pool.query('SELECT * FROM employees WHERE id = ?', [id]);
    return rows[0];
  }

  static async update(id, data) {
    const pool = getPool();
    const query = `
      UPDATE employees 
      SET employee_name = ?, gender = ?, dob = ?, age = ?, department = ?, designation = ?, joining_date = ?, salary = ?, phone = ?, email = ?, address = ?, status = ?
      WHERE id = ?
    `;
    const params = [
      data.employee_name,
      data.gender,
      data.dob,
      data.age,
      data.department,
      data.designation,
      data.joining_date,
      data.salary,
      data.phone,
      data.email,
      data.address,
      data.status,
      id
    ];
    const [result] = await pool.query(query, params);
    return result.affectedRows > 0;
  }

  static async updateStatus(id, status) {
    const pool = getPool();
    const [result] = await pool.query('UPDATE employees SET status = ? WHERE id = ?', [status, id]);
    return result.affectedRows > 0;
  }

  static async softDelete(id) {
    const pool = getPool();
    const [result] = await pool.query('UPDATE employees SET status = "Inactive" WHERE id = ?', [id]);
    return result.affectedRows > 0;
  }
}

module.exports = Employee;
