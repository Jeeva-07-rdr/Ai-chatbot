# TECHNICAL FLOW DOCUMENTATION
## Enterprise Employee Management System (EMS)

---

## 1. Cover Page

*   **Project Name:** Enterprise Employee Management System (EMS)
*   **Technology Stack:** React.js, Node.js, Express.js, MySQL (XAMPP)
*   **Architecture Pattern:** Model-View-Controller (MVC) with RESTful APIs
*   **Developer Workspace:** `C:\employe management`
*   **Version:** v1.2.0 (Redesigned SaaS Interface with Indian Rupee Format)
*   **Documentation Date:** July 8, 2026

---

## Table of Contents
1. [Cover Page](#1-cover-page)
2. [Architecture Overview](#2-architecture-overview)
3. [Complete Folder Structure](#3-complete-folder-structure)
4. [Startup Flow](#4-startup-flow)
5. [Login Flow](#5-login-flow)
6. [Dashboard Flow](#6-dashboard-flow)
7. [Employee Module Flow](#7-employee-module-flow)
8. [Add Employee Flow](#8-add-employee-flow)
9. [Edit Employee Flow](#9-edit-employee-flow)
10. [Delete / Active / Inactive Flow](#10-delete--active--inactive-flow)
11. [Search & Filter Flow](#11-search--filter-flow)
12. [Backend Architecture Flow](#12-backend-architecture-flow)
13. [Database Flow](#13-database-flow)
14. [API Endpoint Documentation](#14-api-endpoint-documentation)
15. [React Component Flow](#15-react-component-flow)
16. [State Management Flow](#16-state-management-flow)
17. [Complete Request Lifecycle](#17-complete-request-lifecycle)
18. [Error Handling Strategy](#18-error-handling-strategy)
19. [Security Implementation Flow](#19-security-implementation-flow)
20. [Performance Optimization Flow](#20-performance-optimization-flow)
21. [Source Code Explanations](#21-source-code-explanations)
22. [Mermaid Sequence Diagrams](#22-mermaid-sequence-diagrams)
23. [Conclusion](#23-conclusion)

---

## 2. Architecture Overview

This application is built on a decoupled, three-tier architecture: client-side view layer, server-side API layer, and database storage layer. It follows the **Model-View-Controller (MVC)** design pattern on the backend, communicating via a **RESTful API** over HTTP.

### Complete Flow Architecture:
```text
User Actions in browser
  │
  ▼
React Frontend (Vite)
  │
  ▼
React Router DOM (Determines active route: '/' or '/employees')
  │
  ▼
Axios API client (Injects JWT authorization headers, transforms JSON requests)
  │
  ▼
Express Route Listener (Maps request endpoints and HTTP methods: GET, POST, etc.)
  │
  ▼
Security / Validation Middlewares (Helmet, CORS, JWT verification, body validations)
  │
  ▼
Controller (Reads requests, manages HTTP statuses, coordinates models, writes responses)
  │
  ▼
Database Model (Generates prepared queries, manages SQL transaction statements)
  │
  ▼
MySQL Database Server (Executes statement, commits data updates, returns table rows)
  │
  ▼
Model returns row objects to Controller
  │
  ▼
Controller sends JSON payload back to Axios
  │
  ▼
React state updates in context/component hooks
  │
  ▼
Browser performs HMR layout repaint (UI updates instantly)
```

---

## 3. Complete Folder Structure

Below is the directory mapping of the EMS system. Each file is grouped into folders aligned with their architectural roles:

### Frontend Layout (`frontend/`)
*   `frontend/public/` - Static assets such as logos and site favicons.
*   `frontend/src/assets/` - Global SVG assets and graphic vectors.
*   `frontend/src/components/` - Reusable UI components.
    *   **Sidebar.jsx**: Collapsible side navigation containing profile avatar card.
    *   **Header.jsx**: Top navbar displaying current breadcrumbs path, clock, and theme toggler.
    *   **EmployeeModal.jsx**: Structured popup forms split into sections using category tabs.
    *   **EmployeeDetailModal.jsx**: Detailed view card containing employee print button.
    *   **ConfirmDialog.jsx**: Modular dialog overlay confirming delete/activation states.
*   `frontend/src/context/` - Auth Context provider.
    *   **AuthContext.jsx**: Stores token state and provides login/logout helpers.
*   `frontend/src/pages/` - Core view frames.
    *   **Login.jsx**: Authentication entry gate form.
    *   **ForgotPassword.jsx**: Handles password reset requests.
    *   **Dashboard.jsx**: Coordinates statistics display or personnel grid directories.
*   `frontend/src/utils/` - API utility wrapper.
    *   **api.js**: Configures default Axios headers and BaseURL.
*   `frontend/src/App.jsx` - Root routing map.
*   `frontend/src/main.jsx` - Bootstraps React rendering lifecycle.
*   `frontend/src/index.css` - Custom styling tokens, layout rules, and variables.

### Backend Layout (`backend/`)
*   `backend/src/config/` - System configuration files.
    *   **db.js**: Manages MySQL connection pool, db generation, and auto-migrations.
*   `backend/src/controllers/` - Route handler methods (Controller).
    *   **authController.js**: Authenticates administrators, seeds password hashes.
    *   **employeeController.js**: CRUD logic controllers for employee records.
*   `backend/src/middleware/` - Request interceptor hooks.
    *   **authMiddleware.js**: Intercepts headers to verify valid JWT payloads.
    *   **validationMiddleware.js**: Sanitizes client inputs using validator chains.
*   `backend/src/models/` - Query models (Model).
    *   **User.js**: Executes User account SQL transactions.
    *   **Employee.js**: Generates Employee database SQL operations.
*   `backend/src/routes/` - Route listener registries.
    *   **authRoutes.js**: Defines authentication routes.
    *   **employeeRoutes.js**: Defines employee directory CRUD endpoints.
*   `backend/src/server.js` - Main entry file starting the NodeJS Express listener.

---

## 4. Startup Flow

Below is the execution flow when launching the full-stack system:

```text
1. Developer executes "npm run dev" in backend/ and frontend/ terminals
    │
    ├─► Backend Startup:
    │     1. nodemon launches src/server.js
    │     2. dotenv loads host environment keys from backend/.env
    │     3. server.js imports cors, helmet, morgan, routes
    │     4. server.js calls initializeDatabase() in config/db.js:
    │          a. Connects to local MySQL (XAMPP port 3306)
    │          b. Creates database "employee_management" if missing
    │          c. Drops "attendance" table if found
    │          d. Verifies "users", "employees", "departments", "settings" tables
    │          e. Seeds default admin: username "admin", password "admin123" (hashed)
    │     5. Express registers routes and launches listening server on port 5000
    │
    └─► Frontend Startup:
          1. vite launches local bundler
          2. Parses vite.config.js and src/main.jsx
          3. Loads App.jsx and mounts AuthProvider context
          4. Checks local storage for token session keys
          5. Opens web browser port 5173
          6. If token exists, redirects to '/'; else redirects to '/login'
```

---

## 5. Login Flow

The authentication process relies on verifying User ID/Password and issuing JSON Web Tokens (JWT) for stateless sessions:

```text
1. User enters username (User ID) and password on Login page (Login.jsx)
    │
    ▼
2. Form submit calls login(username, password) in AuthContext.jsx
    │
    ▼
3. Axios transmits HTTP POST request containing login JSON parameters to backend:
   POST http://localhost:5000/api/auth/login
    │
    ▼
4. Express route listener (authRoutes.js) sends payload to login rules inside:
   validationMiddleware.js (verifies input string variables are not empty)
    │
    ▼
5. Request is forwarded to login controller: authController.js
    │
    ▼
6. Controller calls User.findByUsernameOrEmail(identifier) in models/User.js:
   Runs query: "SELECT * FROM users WHERE username = ? OR email = ?"
    │
    ▼
7. User model returns matched row to Controller
    │
    ▼
8. Controller calls bcrypt.compare(inputPassword, user.password):
   - If match fails: returns 401 Unauthorized JSON error
   - If match succeeds: sign JWT token using jwt.sign() and process.env.JWT_SECRET
    │
    ▼
9. Controller returns response: 200 OK containing jwt token, user role and email
    │
    ▼
10. Frontend AuthContext receives success callback:
    - Stores token and user metadata object in localStorage
    - Navigates client session using navigate('/') to Dashboard
```

---

## 6. Dashboard Flow

When the user is redirected to `/`, the page performs analytics mapping based on the active path:

1.  **Route Evaluation:** **Dashboard.jsx** checks the path using `location.pathname === '/'`. If true, it loads the analytical dashboard view.
2.  **API Data Fetching:** Triggered inside `useEffect` hook:
    *   Calls `api.get('/employees', { params: { status: 'Active', limit: 10000 } })`.
    *   Fetches the active personnel dataset from MySQL database server.
3.  **Metrics Generation:**
    *   `stats.total`: Calculated from total returned rows.
    *   `stats.active`: Sum of profiles matching `status === 'Active'`.
    *   `stats.inactive`: Total rows minus active count.
    *   `stats.departments`: Total distinct department values.
    *   `stats.payroll`: Sum of `salary` fields of active employees divided by 12 (Monthly Payroll).
4.  **UI Layout Mapping:**
    *   Renders 5 metric statistics cards formatted under Indian Rupee standard.
    *   Displays a welcome banner with administrative action buttons.
    *   Renders a read-only list showing the 5 recently registered employee profiles.

---

## 7. Employee Module Flow

When navigation shifts to `/employees`, the page is designed to render directory filters and listing tables:

1.  **Route Detection:** `location.pathname === '/employees'` triggers the directory view.
2.  **Roster Fetching:** Triggers `fetchEmployees()` which requests employees matching the status dropdown state:
    *   `api.get('/employees', { params: { status: statusFilter, limit: 10000 } })`
3.  **UI Loading States:** `loading` state turns true. Table renders shimmer skeleton loaders rather than empty rows.
4.  **Client-Side Processing:** `getProcessedEmployees()` performs live operations on the fetched dataset:
    *   *Search Filter:* Matches search term against ID, name, department, designation, email, and phone.
    *   *Department Filter:* Filters rows matching selected dropdown department.
    *   *Salary Filter:* Segments records matching range criteria (e.g. Under ₹3 Lakhs).
    *   *Column Sorting:* Sorts active table lists by clicked headers (`employee_id`, `employee_name`, `salary`, `age`, etc.) using order direction toggles.
5.  **Pagination:** Divides the filtered array using `currentPage` and `itemsPerPage` configuration variables.
6.  **Table Rendering:** Repaints listing table, mapping badges (with pulsing animations for `Active` users) and action buttons.

---

## 8. Add Employee Flow

The creation flow inserts new profiles into the MySQL database with manual validation hooks:

```text
1. User clicks "+ Add Employee" button -> Modal opens (EmployeeModal.jsx)
    │
    ▼
2. User fills form fields divided across Personal, Employment, Contact, and Status tabs
    │
    ▼
3. User clicks submit -> Form runs client-side JS validator check:
   - Validates that ID, name, joining date, and designation are not empty.
   - Evaluates DOB and requires age >= 18.
   - Confirms email/phone formats.
   - If fields fail: redirects to the tab containing the error and highlights inputs red.
    │
    ▼
4. Successful validator triggers HTTP POST:
   POST http://localhost:5000/api/employees containing JSON body details
    │
    ▼
5. Express Route listener checks auth header using authMiddleware.js (verifies JWT token)
    │
    ▼
6. Request payload passes validationMiddleware.js backend check
    │
    ▼
7. Express calls save controller: employeeController.js (createEmployee)
    │
    ▼
8. Controller calls Employee.create() model:
   Runs: "INSERT INTO employees (employee_id, employee_name, gender, dob, age, department, designation, joining_date, salary, phone, email, address, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    │
    ▼
9. MySQL server creates the database record and returns insertId details
    │
    ▼
10. Controller returns 201 Created status containing profile metadata
    │
    ▼
11. React receives response:
    - Closes EmployeeModal popup
    - Fires success message toast alerts
    - Calls fetchEmployees() to pull updated records and re-render grid
```

---

## 9. Edit Employee Flow

The modification flow reads current records, loads them inside forms, and commits changes:

1.  **Row Click:** User clicks edit icon button on employee row.
2.  **Modal Pre-Loading:** Sets `selectedEmployee` state to active row data. Opens **EmployeeModal.jsx**.
3.  **Form Formatting:** `useEffect` hook splits dates, converts salary values to strings, and populates form sections.
4.  **Edit Submission:** User updates input values and clicks submit. Runs validator, then triggers HTTP PUT request:
    *   `api.put(`/employees/${employee.id}`, formData)`
5.  **Backend Controller Processing:** Router calls `updateEmployee` inside **employeeController.js**.
6.  **SQL Statement Execution:** Controller calls `Employee.update(id, data)`:
    *   Runs: `UPDATE employees SET employee_name = ?, gender = ?, dob = ?, age = ?, department = ?, designation = ?, joining_date = ?, salary = ?, phone = ?, email = ?, address = ?, status = ? WHERE id = ?`
7.  **Response Sync:** Database updates record, server returns `200 OK`, frontend displays toast notification, and fetches updated roster.

---

## 10. Delete / Active / Inactive Flow

This system uses a **Soft Delete** pattern. Deleting an employee updates their status to `Inactive`, keeping their records in the database:

### Soft Deletion Flow:
1.  User clicks the delete trash icon button on active row.
2.  **ConfirmDialog.jsx** prompts confirmation.
3.  Clicking confirm triggers HTTP DELETE request: `api.delete(`/employees/${employee.id}`)`.
4.  Backend router triggers `deleteEmployee` in **employeeController.js**.
5.  Controller calls `Employee.softDelete(id)`:
    *   Runs SQL query: `UPDATE employees SET status = 'Inactive' WHERE id = ?`.
6.  Database updates status, server returns `200 OK`, table refreshes, and the employee is removed from the active directory.

### Quick Status Toggle Flow:
1.  Clicking status badge tags directly triggers status toggles:
    *   Runs HTTP PUT request: `api.put(`/employees/${employee.id}/status`, { status: newStatus })`.
2.  Backend calls `Employee.updateStatus(id, status)`:
    *   Runs query: `UPDATE employees SET status = ? WHERE id = ?`.
3.  Table layout refreshes to reflect changed status.

---

## 11. Search & Filter Flow

The search filters operate instantly on client-side state for a fast, responsive user experience:

```text
User types in Search bar
  │
  ▼
Triggers handleSearchChange(e)
  │
  ▼
Sets search state variable -> Resets currentPage to 1
  │
  ▼
Re-renders Dashboard component
  │
  ▼
getProcessedEmployees() triggers:
  1. Filters local array rawEmployees by search query (checks ID, Name, Dept, Designation)
  2. Applies deptFilter dropdown (e.g. 'Engineering')
  3. Applies salaryFilter range criteria
  4. Sorts resulting rows by active sort key (sortBy)
  │
  ▼
Slices array based on itemsPerPage (Pagination)
  │
  ▼
Repaints grid body with matching rows
```

---

## 12. Backend Architecture Flow

The backend maps routes through middleware validation chains before executing controllers:

```text
    Routes (authRoutes.js / employeeRoutes.js)
                      │
                      ▼
    Middleware Validation (validationMiddleware.js)
                      │
                      ▼
    Authentication Middleware (authMiddleware.js)
                      │
                      ▼
    Controller (authController.js / employeeController.js)
                      │
                      ▼
    Model queries (User.js / Employee.js)
                      │
                      ▼
    Database Pool (db.js config connection)
```
*   **Routes:** Connect client request verbs and paths to middleware chains and final controller execution routines.
*   **Middleware:** Checks header JWT signatures, handles request parameter sanitization, and rejects invalid inputs with HTTP errors.
*   **Controllers:** Parse requests, manage response flows, coordinate Model data fetching, and return JSON responses.
*   **Models:** Houses parameterized SQL statements, keeping controller files clean of raw database query strings.
*   **Database Config:** Holds database pool configurations and executes startup auto-migrations.

---

## 13. Database Flow

The database layer runs on MySQL (XAMPP) and communicates using `mysql2/promise` prepared statements:

*   **Connection Pooling:** Initializes a pool of 10 connections in **db.js**. This allows reuse of active database connections, improving query execution speeds.
*   **Prepared Statements:** SQL operations use query placeholders (`?`) to prevent SQL Injection attacks.
*   **Core Queries:**
    *   *Create User:* `INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)`
    *   *Lookup User:* `SELECT * FROM users WHERE username = ? OR email = ?`
    *   *Create Employee:* `INSERT INTO employees (employee_id, employee_name, gender, dob, age, department, designation, joining_date, salary, phone, email, address, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    *   *List Employees:* `SELECT * FROM employees WHERE status = ?`
    *   *Update Employee:* `UPDATE employees SET employee_name = ?, gender = ?, dob = ?, age = ?, department = ?, designation = ?, joining_date = ?, salary = ?, phone = ?, email = ?, address = ?, status = ? WHERE id = ?`
    *   *Soft Delete:* `UPDATE employees SET status = 'Inactive' WHERE id = ?`

---

## 14. API Endpoint Documentation

Below is the REST API documentation for the backend endpoints:

| Method | Endpoint | Purpose | Request Body (JSON) | Response (JSON) | Controller | Database Query |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/auth/login` | Administrator Auth | `{ username, password }` | `{ token, user: { username, email } }` | `authController.login` | `SELECT * FROM users WHERE username = ? OR email = ?` |
| **GET** | `/api/employees` | Fetch Roster List | *None* | `{ employees: [...] }` | `employeeController.getEmployees` | `SELECT * FROM employees WHERE status = ?` |
| **POST** | `/api/employees` | Create New Profile | `{ employee_id, employee_name, gender, dob, age, department, designation, joining_date, salary, phone, email, address, status }` | `{ message, employee }` | `employeeController.createEmployee` | `INSERT INTO employees (...) VALUES (...)` |
| **PUT** | `/api/employees/:id` | Update Profile Details | `{ employee_name, gender, dob, age, department, designation, joining_date, salary, phone, email, address, status }` | `{ message, employee }` | `employeeController.updateEmployee` | `UPDATE employees SET ... WHERE id = ?` |
| **DELETE** | `/api/employees/:id` | Soft Delete Employee | *None* | `{ message }` | `employeeController.deleteEmployee` | `UPDATE employees SET status = 'Inactive' WHERE id = ?` |
| **PUT** | `/api/employees/:id/status` | Quick Status Toggle | `{ status }` | `{ message, employee }` | `employeeController.updateStatus` | `UPDATE employees SET status = ? WHERE id = ?` |

---

## 15. React Component Flow

Here is the structural hierarchy of components, detailing their properties, hooks, and local states:

### 1. **App.jsx** (Root Route Controller)
*   **Parent:** Root DOM node bootstrap.
*   **Child Components:** `Login`, `ForgotPassword`, `Dashboard` (guarded by contexts).
*   **State / Contexts:** `AuthProvider` wrapper container.
*   **Hooks Used:** Routing elements mapping hooks.

### 2. **Dashboard.jsx** (Central Control Panel)
*   **Parent:** `App` route container.
*   **Child Components:** `Sidebar`, `Header`, `EmployeeModal`, `EmployeeDetailModal`, `ConfirmDialog`.
*   **States Managed:**
    *   `rawEmployees` (runtimes array list)
    *   `search`, `statusFilter`, `deptFilter`, `salaryFilter` (active search criteria)
    *   `sortBy` / `order` (sort options)
    *   `currentPage` / `itemsPerPage` (pagination offsets)
    *   `stats` (metrics calculations state object)
*   **Hooks Used:** `useLocation`, `useState`, `useEffect`.

### 3. **Sidebar.jsx** (Drawer Menu Container)
*   **Parent:** `Dashboard` frame.
*   **Child Components:** Navigation links.
*   **States Managed:** `isCollapsed` (toggles width and layout classes).
*   **Hooks Used:** `useAuth` context reading, `useState`, `useEffect`.

### 4. **Header.jsx** (Topbar Dashboard Navbar)
*   **Parent:** `Dashboard` frame.
*   **Child Components:** Dropdown actions menu.
*   **States Managed:** `timeString` (updates clock), `isProfileMenuOpen` (toggle menu), `isDarkMode` (toggle light/dark theme class).
*   **Hooks Used:** `useAuth`, `useState`, `useEffect`, `useRef`.

### 5. **EmployeeModal.jsx** (Add/Edit Tab Form)
*   **Parent:** `Dashboard` modal overlay.
*   **Props Received:** `isOpen`, `employee`, `onSave`, `onClose`.
*   **States Managed:** `activeTab` (switches form sections), `formData` (stores input values), `errors` (stores validation states).
*   **Hooks Used:** `useState`, `useEffect`.

---

## 16. State Management Flow

The application manages state through local states, component properties, and global context providers:

### Local Component States
Component-specific UI states (like modal visibility, dropdown states, and search queries) are managed using the `useState` hook. These states do not need to be shared globally.

### Global Auth Context (**AuthContext.jsx**)
The authentication state is shared globally across the app using React Context:
```javascript
const AuthContext = createContext();
```
*   **State Variables:**
    *   `user`: Stores active administrator details (User ID, email, role).
    *   `token`: JWT authentication token.
    *   `loading`: Boolean flag showing if user session checks are active.
    *   `toast`: Custom configuration details for toast alerts.
*   **Auth State Sync:** The context checks `localStorage` on mount to resume previous sessions. It provides helper methods like `login()`, `logout()`, and `showToast()` to all children.

---

## 17. Complete Request Lifecycle

Below is the request-response lifecycle sequence, showing how an API call travels from the UI to the database and back:

```text
[ Browser UI ]        [ Axios Client ]      [ Express Server ]     [ MySQL Database ]
     │                       │                      │                       │
     │── 1. User Action ────►│                      │                       │
     │   (e.g., Load Table)  │                      │                       │
     │                       │── 2. HTTP GET ──────►│                       │
     │                       │   (Auth Token)       │                       │
     │                       │                      │── 3. Check JWT Token ─│
     │                       │                      │   (authMiddleware)    │
     │                       │                      │                       │
     │                       │                      │── 4. Query Database ─►│
     │                       │                      │   (Employee.findAll)  │
     │                       │                      │                       │
     │                       │                      │◄── 5. Returns Rows ───│
     │                       │                      │                       │
     │                       │◄── 6. JSON Response ─│                       │
     │                       │   (200 OK)           │                       │
     │◄── 7. Update State ───│                      │                       │
     │   (Re-render table)   │                      │                       │
```

---

## 18. Error Handling Strategy

The application handles errors gracefully across all layers of the stack:

*   **Client Validation:** The form checks input fields for invalid data (e.g. age under 18) before sending the request. It highlights errors in red and switches tabs to direct the user to the invalid field.
*   **API Middleware validation:** The backend uses `express-validator` to scan requests, returning a `400 Bad Request` JSON error containing validation details if invalid parameters are found.
*   **SQL Exceptions:** Database queries are wrapped in `try/catch` blocks. If a query fails, the error is logged on the server and a `500 Internal Server Error` is returned to the client, preventing database leaks.
*   **Auth Failures:** If login fails or a token is invalid, the API returns a `401 Unauthorized` response, prompting the frontend to redirect the user to `/login`.
*   **Client Notification Toasts:** Custom sliding toast alerts display clear success or error messages in the bottom-right corner of the screen.

---

## 19. Security Flow

The system implements multiple security layers to protect the application and database:

*   **JWT Authentication:** User sessions are stateless and secured using JWT. Tokens are verified on every protected API call using **authMiddleware.js**.
*   **Password Hashing:** Passwords are never stored in plaintext. They are salted and hashed using bcrypt (10 rounds) before being saved to the database.
*   **SQL Injection Defense:** All queries use prepared statements and parameters (`?` placeholders). This separates SQL code from data parameters, preventing SQL injection.
*   **XSS & Clickjacking Protection:** Helmet middleware is registered globally in Express to configure secure HTTP response headers.
*   **CORS Configuration:** Restricts cross-origin requests to authorized origins (the frontend dev port `http://localhost:5173`).

---

## 20. Performance Optimization Flow

*   **Connection Pooling:** The backend database connection is pooled, avoiding the overhead of opening and closing database connections for every query.
*   **Client-Side Grid Calculations:** Roster search queries, department filtering, salary filtering, and list sorting are processed on the client side. This reduces database queries and server load, providing a fast, lag-free user experience.
*   **Paginated Table Slices:** The frontend table slices the local array to display only the current page's rows. This avoids rendering large datasets and maintains smooth UI performance.
*   **Vite Compiler:** Built on Vite using esbuild for fast builds and hot module replacement (HMR).

---

## 21. Source Code Explanations

Here is a technical summary of the key files in the codebase, explaining their purpose and implementation:

### Backend Controllers

#### 1. **server.js**
*   **Purpose:** Configures the NodeJS server, registers global middleware, imports routes, and starts the Express listener.
*   **How it works:** Initializes Express, registers security middlewares (CORS, Helmet, Morgan logger), imports route maps, and mounts them under `/api/auth` and `/api/employees`. It runs `initializeDatabase()` on startup.

#### 2. **db.js**
*   **Purpose:** Establishes the database connection pool, creates database tables, and handles auto-migrations.
*   **How it works:** Connects to MySQL, creates the database if it is missing, runs queries to verify tables, drops the `attendance` table, and seeds the default admin user with a hashed password.

#### 3. **authController.js**
*   **Purpose:** Coordinates login verification, forgot-password, and reset-password operations.
*   **How it works:** `login` checks for credentials using `User.findByUsernameOrEmail`. It compares password hashes using bcrypt and returns a JWT token if authentication succeeds.

#### 4. **employeeController.js**
*   **Purpose:** Implements CRUD logic for employee profiles.
*   **How it works:** Houses methods like `getEmployees`, `createEmployee`, `updateEmployee`, `deleteEmployee`, and `updateStatus` that map incoming requests to SQL Model commands.

### Frontend Components

#### 5. **Dashboard.jsx**
*   **Purpose:** Handles page layouts, metrics calculations, grid filtering, pagination, and modals coordination.
*   **How it works:** Reads the current URL path. Renders the overview dashboard layout on `/`, and the directory grid layout on `/employees`.

#### 6. **EmployeeModal.jsx**
*   **Purpose:** Form wizard popup for registering or editing employee details.
*   **How it works:** Displays form fields across four tabs. Includes input validation checks and handles submission payloads.

---

## 22. Mermaid Sequence Diagrams

Below are text-based flowcharts representing execution lifecycles:

### 1. Server Startup Flowchart:
```text
[Start npm run dev]
        │
        ▼
[dotenv loads .env]
        │
        ▼
[db.js establishes connection pool]
        │
        ▼
[Runs migration: Drops attendance table]
        │
        ▼
[Verifies users / employees tables schema]
        │
        ▼
[Seeds admin account admin/admin123]
        │
        ▼
[Express registers routes and starts listener]
```

### 2. Employee CRUD Flowchart:
```text
User Actions ────► React UI ────► Axios HTTP Request ────► Backend Controller ────► Database Query
  ▲                                                                                      │
  │                                                                                      ▼
Repaint DOM ◄──── Updates State ◄──── Returns JSON ◄───── Returns Result ◄───── MySQL executes
```

---

## 23. Conclusion

The **Enterprise Employee Management System (EMS)** is structured as a decoupled, MVC full-stack application.

When the server starts, it initializes a MySQL connection pool and runs database table migrations. Users log in securely using username credentials, verified against bcrypt hashes. Successful authentication issues a JWT session token, stored in the user's browser.

The client UI renders dynamically based on routes. The Dashboard (`/`) displays metric calculations, and the Directory (`/employees`) handles personnel listing, advanced filtering, and CRUD operations. All API calls are validated, secured, and processed using parameterized SQL queries, ensuring a secure and reliable application lifecycle.
