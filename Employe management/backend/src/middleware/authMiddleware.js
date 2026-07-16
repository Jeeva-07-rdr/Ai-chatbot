const jwt = require('jsonwebtoken');

module.exports = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    console.warn('API Warning: Unauthorized request - Token missing');
    return res.status(401).json({ message: 'Access denied. Token missing.' });
  }

  try {
    const verified = jwt.verify(token, process.env.JWT_SECRET || 'super_secret_jwt_key_12345!@#');
    req.user = verified;
    next();
  } catch (error) {
    console.error('API Errors / Token Verification Failed:', error.message);
    res.status(403).json({ message: 'Invalid or expired token.' });
  }
};
