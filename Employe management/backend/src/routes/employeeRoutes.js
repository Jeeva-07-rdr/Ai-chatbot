const express = require('express');
const router = express.Router();
const employeeController = require('../controllers/employeeController');
const authMiddleware = require('../middleware/authMiddleware');
const { employeeValidation } = require('../middleware/validationMiddleware');

// All employee routes require authorization
router.use(authMiddleware);

router.get('/', employeeController.getEmployees);
router.post('/', employeeValidation, employeeController.createEmployee);
router.get('/:id', employeeController.getEmployeeById);
router.put('/:id', employeeValidation, employeeController.updateEmployee);
router.delete('/:id', employeeController.deleteEmployee);
router.put('/:id/status', employeeController.updateStatus);

module.exports = router;
