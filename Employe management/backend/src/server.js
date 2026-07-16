const app = require('./app');
const { initializeDatabase } = require('./config/db');
require('dotenv').config();

const PORT = process.env.PORT || 5000;

async function startServer() {
  try {
    // Initialize Database first (Creates DB, Tables, Seeds default users)
    await initializeDatabase();

    // Start Express Server listening
    app.listen(PORT, () => {
      console.log(`Server Started: Express server running on port ${PORT}`);
    });

  } catch (error) {
    console.error('API Errors / Server failed to start:', error);
    process.exit(1);
  }
}

startServer();
