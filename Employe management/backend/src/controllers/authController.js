const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const User = require('../models/User');

exports.login = async (req, res) => {
  const { username, password } = req.body;

  try {
    const user = await User.findByUsernameOrEmail(username);
    if (!user) {
      console.warn('Login Failed: User not found for User ID:', username);
      return res.status(401).json({ message: 'Invalid User ID or password' });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      console.warn('Login Failed: Incorrect password for User ID:', username);
      return res.status(401).json({ message: 'Invalid User ID or password' });
    }

    // Generate JWT
    const token = jwt.sign(
      { id: user.id, username: user.username, email: user.email, role: user.role },
      process.env.JWT_SECRET || 'super_secret_jwt_key_12345!@#',
      { expiresIn: process.env.JWT_EXPIRES_IN || '24h' }
    );

    console.log('Login Success: Admin logged in successfully:', username);

    return res.status(200).json({
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role
      }
    });

  } catch (error) {
    console.error('SQL Errors / API Errors - Login exception:', error);
    return res.status(500).json({ message: 'Internal server error occurred.' });
  }
};

exports.forgotPassword = async (req, res) => {
  const { username } = req.body;

  try {
    const user = await User.findByUsernameOrEmail(username);
    if (!user) {
      console.warn('Forgot Password Failed: User ID does not exist:', username);
      return res.status(404).json({ message: 'No account associated with this User ID exists.' });
    }

    console.log('Forgot Password Verification Passed: User ID verified:', username);
    return res.status(200).json({ message: 'User ID verified. You may reset your password.' });

  } catch (error) {
    console.error('SQL Errors / API Errors - Forgot password exception:', error);
    return res.status(500).json({ message: 'Internal server error occurred.' });
  }
};

exports.resetPassword = async (req, res) => {
  const { username, newPassword } = req.body;

  try {
    const user = await User.findByUsernameOrEmail(username);
    if (!user) {
      console.warn('Reset Password Failed: User ID does not exist:', username);
      return res.status(404).json({ message: 'No account associated with this User ID exists.' });
    }

    const hashedPassword = await bcrypt.hash(newPassword, 10);
    const success = await User.updatePassword(username, hashedPassword);

    if (success) {
      console.log('Password Reset Success for User ID:', username);
      return res.status(200).json({ message: 'Password updated successfully in database.' });
    } else {
      console.warn('Password Reset Failed in DB query update:', username);
      return res.status(400).json({ message: 'Failed to update the password.' });
    }

  } catch (error) {
    console.error('SQL Errors / API Errors - Reset password exception:', error);
    return res.status(500).json({ message: 'Internal server error occurred.' });
  }
};
