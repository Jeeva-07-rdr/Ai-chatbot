const mysql = require('mysql2/promise');
const bcrypt = require('bcryptjs');
require('dotenv').config();

const { DB_HOST, DB_USER, DB_PASS, DB_NAME } = process.env;

let pool;

async function initializeDatabase() {
  try {
    // 1. Connect to MySQL server without database first
    const connection = await mysql.createConnection({
      host: DB_HOST || 'localhost',
      user: DB_USER || 'root',
      password: DB_PASS || ''
    });

    console.log('Database Connected (Server connection established)');

    // 2. Create database if it doesn't exist
    await connection.query(`CREATE DATABASE IF NOT EXISTS \`${DB_NAME || 'employee_management'}\``);
    console.log(`Database "${DB_NAME || 'employee_management'}" ensured`);
    await connection.end();

    // 3. Connect to the specific database using a pool
    pool = mysql.createPool({
      host: DB_HOST || 'localhost',
      user: DB_USER || 'root',
      password: DB_PASS || '',
      database: DB_NAME || 'employee_management',
      waitForConnections: true,
      connectionLimit: 10,
      queueLimit: 0
    });

    // 4. Create Tables
    await createTables();

    // 5. Seed initial admin
    await seedAdmin();

  } catch (error) {
    console.error('SQL Errors / Database Connection Failed:', error);
    process.exit(1);
  }
}

async function createTables() {
  // Departments table
  await pool.query(`
    CREATE TABLE IF NOT EXISTS departments (
      id INT AUTO_INCREMENT PRIMARY KEY,
      name VARCHAR(100) UNIQUE NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
  `);

  // Drop old users table if it doesn't have the username column
  try {
    const [cols] = await pool.query(`SHOW COLUMNS FROM users LIKE 'username'`);
    if (cols.length === 0) {
      await pool.query(`DROP TABLE IF EXISTS users`);
      console.log('Upgrading users schema: Old users table dropped');
    }
  } catch (err) {
    // Table doesn't exist yet, which is fine
  }

  // Users table
  await pool.query(`
    CREATE TABLE IF NOT EXISTS users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(100) UNIQUE NOT NULL,
      email VARCHAR(100) UNIQUE NOT NULL,
      password VARCHAR(255) NOT NULL,
      role ENUM('Super Admin', 'Admin') DEFAULT 'Admin',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
  `);

  // Employees table
  await pool.query(`
    CREATE TABLE IF NOT EXISTS employees (
      id INT AUTO_INCREMENT PRIMARY KEY,
      employee_id VARCHAR(50) UNIQUE NOT NULL,
      employee_name VARCHAR(100) NOT NULL,
      gender ENUM('Male', 'Female', 'Other') NOT NULL,
      dob DATE NOT NULL,
      age INT NOT NULL,
      department VARCHAR(100) NOT NULL,
      designation VARCHAR(100) NOT NULL,
      joining_date DATE NOT NULL,
      salary DECIMAL(12, 2) NOT NULL,
      phone VARCHAR(20) UNIQUE NOT NULL,
      email VARCHAR(100) UNIQUE NOT NULL,
      address TEXT NOT NULL,
      status ENUM('Active', 'Inactive') DEFAULT 'Active',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
  `);

  // Drop attendance table as requested
  await pool.query(`DROP TABLE IF EXISTS attendance;`);
  console.log('Database tables upgraded: attendance table dropped/removed');

  // Settings table
  await pool.query(`
    CREATE TABLE IF NOT EXISTS settings (
      id INT AUTO_INCREMENT PRIMARY KEY,
      key_name VARCHAR(100) UNIQUE NOT NULL,
      key_value TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
  `);

  console.log('Database tables verified/created successfully');
}

async function seedAdmin() {
  const [rows] = await pool.query('SELECT * FROM users LIMIT 1');
  if (rows.length === 0) {
    const adminUsername = 'admin';
    const adminEmail = 'admin@enterprise.com';
    const adminPassword = 'admin123';
    const hashedPassword = await bcrypt.hash(adminPassword, 10);
    await pool.query(
      'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
      [adminUsername, adminEmail, hashedPassword, 'Admin']
    );
    console.log('Seeded default admin user: username: admin / email: admin@enterprise.com / password: admin123');

    // Also seed some default departments to make selection nice
    const defaultDepts = ['Human Resources', 'Engineering', 'Marketing', 'Sales', 'Finance'];
    for (const dept of defaultDepts) {
      await pool.query('INSERT IGNORE INTO departments (name) VALUES (?)', [dept]);
    }
    console.log('Seeded default departments');
  }
}

module.exports = {
  initializeDatabase,
  getPool: () => {
    if (!pool) {
      throw new Error('Database pool not initialized. Call initializeDatabase first.');
    }
    return pool;
  }
};
