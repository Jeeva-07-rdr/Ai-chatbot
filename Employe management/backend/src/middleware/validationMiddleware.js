const { body, validationResult } = require('express-validator');

// Middleware to capture express-validator errors and send bad request responses
const validate = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    console.error('API Errors / Validation failed:', errors.array());
    return res.status(400).json({ errors: errors.array() });
  }
  next();
};

const loginValidation = [
  body('username').notEmpty().withMessage('User ID is required'),
  body('password').notEmpty().withMessage('Password is required'),
  validate
];

const forgotPasswordValidation = [
  body('username').notEmpty().withMessage('User ID is required'),
  validate
];

const resetPasswordValidation = [
  body('username').notEmpty().withMessage('User ID is required'),
  body('newPassword').isLength({ min: 6 }).withMessage('Password must be at least 6 characters long'),
  validate
];

const employeeValidation = [
  body('employee_id').notEmpty().withMessage('Employee ID is required'),
  body('employee_name').notEmpty().trim().withMessage('Employee name is required'),
  body('gender').isIn(['Male', 'Female', 'Other']).withMessage('Gender must be Male, Female, or Other'),
  body('dob').isISO8601().withMessage('Date of birth must be a valid date (YYYY-MM-DD)'),
  body('age').isInt({ min: 18, max: 100 }).withMessage('Age must be between 18 and 100'),
  body('department').notEmpty().withMessage('Department is required'),
  body('designation').notEmpty().withMessage('Designation is required'),
  body('joining_date').isISO8601().withMessage('Joining date must be a valid date (YYYY-MM-DD)'),
  body('salary').isNumeric({ no_symbols: true }).withMessage('Salary must be numeric and not contain symbols'),
  body('phone').isMobilePhone().withMessage('Phone number must be a valid phone number'),
  body('email').isEmail().withMessage('Email must be a valid email address'),
  body('address').notEmpty().withMessage('Address is required'),
  body('status').optional().isIn(['Active', 'Inactive']).withMessage('Status must be Active or Inactive'),
  validate
];

module.exports = {
  loginValidation,
  forgotPasswordValidation,
  resetPasswordValidation,
  employeeValidation
};
