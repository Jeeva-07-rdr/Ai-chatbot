# Enterprise Employee Management System (EMS)

A secure, responsive, and modern Full-Stack Employee Management System built using React.js, Node.js, Express.js, and MySQL (via XAMPP). The application implements an active/inactive status toggle system, soft delete, multi-column sorting, advanced search, filtering, and session management using JWT.

---

## Folder Structure

```
/employe management
├── backend/
│   ├── src/
│   │   ├── config/          # Database configuration (db.js)
│   │   ├── controllers/     # Route controllers (authController.js, employeeController.js)
│   │   ├── middleware/      # Middlewares (authMiddleware.js, validationMiddleware.js)
│   │   ├── models/          # MVC Models (User.js, Employee.js)
│   │   ├── routes/          # Express Routers (authRoutes.js, employeeRoutes.js)
│   │   ├── app.js           # Express App configuration
│   │   └── server.js        # Backend entry file
│   ├── .env.example         # Template for environment settings
│   ├── package.json         # Node.js backend dependencies
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/      # Common UI components (Header, Sidebar, Modals, ConfirmDialog)
│   │   ├── context/         # Auth and Toast notifications context
│   │   ├── pages/           # Pages (Login, ForgotPassword, Dashboard)
│   │   ├── utils/           # API config (Axios wrapper api.js)
│   │   ├── App.jsx          # Route control
│   │   ├── index.css        # Premium Vanilla CSS layout
│   │   └── main.jsx         # Client entry point
│   ├── index.html           # Main HTML bootstrap wrapper
│   ├── package.json         # Node.js frontend dependencies
│   └── vite.config.js       # Vite bundler config
├── node-portable/           # Bundled Node.js portable folder (if global Node is absent)
├── employee_management.sql  # Database dump file
├── INSTALL.md               # Complete XAMPP & run commands guide
└── README.md                # Project documentation (this file)
```

---

## API Documentation

All API endpoints are prefixed with `/api`.

### Authentication Endpoints (`/api/auth`)
* **POST `/api/auth/login`**: Sign in administrator.
  * *Request Body:* `{ "username": "admin", "password": "admin123" }`
  * *Response (200 OK):* `{ "token": "JWT_TOKEN_HERE", "user": { "id": 1, "username": "admin", "email": "admin...", "role": "Admin" } }`
* **POST `/api/auth/forgot-password`**: Check if User ID is registered.
  * *Request Body:* `{ "username": "admin" }`
* **POST `/api/auth/reset-password`**: Reset/update administrator password.
  * *Request Body:* `{ "username": "admin", "newPassword": "new_password" }`

### Employee Endpoints (`/api/employees`)
*All employee endpoints require a valid JWT token attached to the `Authorization` header as `Bearer <token>`.*

* **GET `/api/employees`**: Get employees matching filters.
  * *Query Params (Optional):*
    - `status` (Values: `Active` [default], `Inactive`, `All`)
    - `search` (Search string matches ID, name, email, phone, department)
    - `sortBy` (Values: `employee_id`, `employee_name`, `department`, `designation`, `salary`, `phone`, `email`, `status`, `created_at` [default])
    - `order` (Values: `ASC`, `DESC` [default])
    - `page` (Default: `1`)
    - `limit` (Default: `10`)
  * *Response:* `{ "employees": [...], "pagination": { "total": 12, "page": 1, "limit": 10, "totalPages": 2 } }`
* **POST `/api/employees`**: Create new employee record.
  * *Request Body:* Complete details (employee_id, employee_name, gender, dob, age, department, designation, joining_date, salary, phone, email, address, status).
* **GET `/api/employees/:id`**: Fetch detailed profile of a single employee.
* **PUT `/api/employees/:id`**: Update existing employee details.
* **DELETE `/api/employees/:id`**: Soft-delete employee. Changes `status` to `Inactive`.
* **PUT `/api/employees/:id/status`**: Toggle/update status manually.
  * *Request Body:* `{ "status": "Active" }` or `{ "status": "Inactive" }`

---

## Core Features & Active/Inactive Logic
1. **Soft Delete**: When delete is clicked, the status changes to `Inactive` in MySQL. Records are never permanently removed (except by future Super Admin feature).
2. **Badge Toggles**: Badges in the table show `Active` (Green) or `Inactive` (Red). Clicking the badge prompts a confirmation popup to toggle employment status.
3. **Filter System**: Default view loads only `Active` employees. Changing the dropdown to `Inactive` or `All` loads matching records with API parameters.

---

## Default Login Credentials
- **User ID:** `admin`
- **Password:** `admin123`
