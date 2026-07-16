# XAMPP & Project Setup Guide

Follow this guide to get the **Enterprise Employee Management System** running locally.

---

## 1. XAMPP and phpMyAdmin Setup

### Install XAMPP
1. Download and install **XAMPP** from [Apache Friends](https://www.apachefriends.org/).
2. Run the **XAMPP Control Panel**.
3. Start the **Apache** and **MySQL** modules. They should turn green, indicating they are running.

### Configure phpMyAdmin (Optional)
The system is designed to **automatically** create the database and tables on backend startup, so you do not need to create them manually! However, if you wish to do so or inspect the database:
1. Open your browser and navigate to `http://localhost/phpmyadmin`.
2. To create the database manually, click **New** on the left menu, enter `employee_management` in the Database name field, and click **Create**.
3. Alternatively, you can click the **Import** tab, select the `employee_management.sql` script located in the project root folder, and click **Go** to seed the schema and admin credentials.

---

## 2. Project Installation

### Step 1: Install Dependencies
Open your command terminal (Command Prompt or PowerShell) and run the following commands:

**For the Backend:**
```bash
cd backend
npm install
```

**For the Frontend:**
```bash
cd ../frontend
npm install
```

*(Note: If Node.js/NPM is not installed globally on your machine, you can run the commands using the bundled portable Node environment in the project directory, as detailed in Section 4 below).*

---

## 3. Running the Project

You need to run **both** the backend server and frontend development server simultaneously.

### Run Backend Server
From the `backend` folder, run:
```bash
npm run dev
```
You should see:
- `Database Connected (Server connection established)`
- `Database "employee_management" ensured`
- `Database tables verified/created successfully`
- `Server Started: Express server running on port 5000`

### Run Frontend Client
Open a second terminal window, navigate to the `frontend` folder, and run:
```bash
npm run dev
```
This will start the Vite server. Open the displayed local address (usually `http://localhost:5173`) in your web browser.

---

## 4. Run Using Portable Node (Troubleshooting)

If Node.js is not installed on your system, you can use the portable Node version that has been downloaded in `c:\employe management\node-portable\`.

### Set PATH in PowerShell (Recommended)
Before running commands in your terminal, run this to enable `node`, `npm`, and `npx` locally:
```powershell
$env:PATH = "c:\employe management\node-portable;" + $env:PATH
```

Now, you can run standard commands directly in that terminal window:
```powershell
# For Backend
cd backend
npm install
npm run dev

# For Frontend (In a new terminal window after setting PATH)
cd frontend
npm install
npm run dev
```
