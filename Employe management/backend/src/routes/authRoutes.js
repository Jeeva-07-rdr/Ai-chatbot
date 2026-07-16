const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');
const { loginValidation, forgotPasswordValidation, resetPasswordValidation } = require('../middleware/validationMiddleware');

router.post('/login', loginValidation, authController.login);
router.post('/forgot-password', forgotPasswordValidation, authController.forgotPassword);
router.post('/reset-password', resetPasswordValidation, authController.resetPassword);

module.exports = router;
