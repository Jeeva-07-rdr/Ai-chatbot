const { getPool } = require('../config/db');

class User {
  static async findByUsernameOrEmail(identifier) {
    const pool = getPool();
    const [rows] = await pool.query('SELECT * FROM users WHERE username = ? OR email = ?', [identifier, identifier]);
    return rows[0];
  }

  static async findById(id) {
    const pool = getPool();
    const [rows] = await pool.query('SELECT * FROM users WHERE id = ?', [id]);
    return rows[0];
  }

  static async updatePassword(identifier, newHashedPassword) {
    const pool = getPool();
    const [result] = await pool.query(
      'UPDATE users SET password = ? WHERE username = ? OR email = ?',
      [newHashedPassword, identifier, identifier]
    );
    return result.affectedRows > 0;
  }
}

module.exports = User;
