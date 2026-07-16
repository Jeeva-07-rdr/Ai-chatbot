const Employee = require('../models/Employee');

exports.createEmployee = async (req, res) => {
  try {
    const { employee_id, email, phone } = req.body;

    // Check unique constraints
    const duplicate = await Employee.checkUnique({ employee_id, email, phone });
    if (duplicate) {
      console.warn(`API Errors - Employee creation validation failed: duplicate ${duplicate.type}`);
      return res.status(400).json({ message: duplicate.message, field: duplicate.type });
    }

    const newId = await Employee.create(req.body);
    console.log(`Employee Created: Successfully registered employee ID ${employee_id} (DB ID: ${newId})`);

    return res.status(201).json({
      message: 'Employee created successfully',
      employeeId: newId
    });

  } catch (error) {
    console.error('SQL Errors / API Errors - Create employee exception:', error);
    return res.status(500).json({ message: 'Internal server error during employee creation.' });
  }
};

exports.getEmployees = async (req, res) => {
  try {
    const { status, search, sortBy, order, page, limit } = req.query;

    const result = await Employee.findAll({
      status: status || 'Active', // Default is Active
      search: search || '',
      sortBy: sortBy || 'created_at',
      order: order || 'DESC',
      page: page || 1,
      limit: limit || 10
    });

    return res.status(200).json(result);

  } catch (error) {
    console.error('SQL Errors / API Errors - Fetch employees exception:', error);
    return res.status(500).json({ message: 'Internal server error while fetching employees.' });
  }
};

exports.getEmployeeById = async (req, res) => {
  try {
    const employee = await Employee.findById(req.params.id);
    if (!employee) {
      return res.status(404).json({ message: 'Employee not found' });
    }
    return res.status(200).json(employee);
  } catch (error) {
    console.error('SQL Errors / API Errors - Fetch single employee exception:', error);
    return res.status(500).json({ message: 'Internal server error while fetching employee details.' });
  }
};

exports.updateEmployee = async (req, res) => {
  try {
    const { id } = req.params;
    const { employee_id, email, phone } = req.body;

    // Verify employee exists
    const existing = await Employee.findById(id);
    if (!existing) {
      return res.status(404).json({ message: 'Employee not found' });
    }

    // Check unique constraints (excluding this employee)
    const duplicate = await Employee.checkUnique({ employee_id, email, phone, excludeId: id });
    if (duplicate) {
      console.warn(`API Errors - Employee update validation failed: duplicate ${duplicate.type}`);
      return res.status(400).json({ message: duplicate.message, field: duplicate.type });
    }

    const success = await Employee.update(id, req.body);
    if (success) {
      console.log(`Employee Updated: Successfully edited employee ID ${employee_id}`);
      return res.status(200).json({ message: 'Employee updated successfully' });
    } else {
      return res.status(400).json({ message: 'Failed to update employee details (no changes or update error).' });
    }

  } catch (error) {
    console.error('SQL Errors / API Errors - Update employee exception:', error);
    return res.status(500).json({ message: 'Internal server error while updating employee.' });
  }
};

exports.deleteEmployee = async (req, res) => {
  try {
    const { id } = req.params;

    const existing = await Employee.findById(id);
    if (!existing) {
      return res.status(404).json({ message: 'Employee not found' });
    }

    // Soft delete - set status to Inactive
    const success = await Employee.softDelete(id);
    if (success) {
      console.log(`Employee Deleted: Soft deleted employee ID ${existing.employee_id} (Status updated to Inactive)`);
      return res.status(200).json({ message: 'Employee soft-deleted successfully' });
    } else {
      return res.status(400).json({ message: 'Failed to delete employee record.' });
    }

  } catch (error) {
    console.error('SQL Errors / API Errors - Delete employee exception:', error);
    return res.status(500).json({ message: 'Internal server error while deleting employee.' });
  }
};

exports.updateStatus = async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    if (!['Active', 'Inactive'].includes(status)) {
      return res.status(400).json({ message: 'Invalid status value. Must be Active or Inactive.' });
    }

    const existing = await Employee.findById(id);
    if (!existing) {
      return res.status(404).json({ message: 'Employee not found' });
    }

    const success = await Employee.updateStatus(id, status);
    if (success) {
      if (status === 'Active') {
        console.log(`Employee Activated: Employee ID ${existing.employee_id} status is now Active`);
      } else {
        console.log(`Employee Deactivated: Employee ID ${existing.employee_id} status is now Inactive`);
      }
      return res.status(200).json({ message: `Employee status updated to ${status} successfully` });
    } else {
      return res.status(400).json({ message: 'Failed to update employee status.' });
    }

  } catch (error) {
    console.error('SQL Errors / API Errors - Update status exception:', error);
    return res.status(500).json({ message: 'Internal server error while updating employee status.' });
  }
};
