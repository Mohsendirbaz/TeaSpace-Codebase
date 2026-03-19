const { spawn } = require('child_process');
const path = require('path');
const express = require('express');
const cors = require('cors');

// Create an Express app for the master server
const app = express();
app.use(cors());

// Define the services to start
const services = [
  {
    name: 'Parameter Append Server',
    command: 'node',
    args: [path.join(__dirname, 'submit_parameter_append.js')],
    port: 3040
  },
  {
    name: 'Complete Set Server',
    command: 'node',
    args: [path.join(__dirname, 'submitCompleteSet.js')],
    port: 3052
  },
  {
    name: 'Formatter Server',
    command: 'python',
    args: [path.join(__dirname, 'formatter.py'), '1', 'server'],
    port: 3050
  },
  {
    name: 'Module1 Server',
    command: 'python',
    args: [path.join(__dirname, 'module1.py'), '1', 'server'],
    port: 3051
  },
  {
    name: 'Config Modules Server',
    command: 'python',
    args: [path.join(__dirname, 'config_modules.py'), '1', 'server'],
    port: 3053
  },
  {
    name: 'Table Server',
    command: 'python',
    args: [path.join(__dirname, 'Table.py'), '1', 'server'],
    port: 3054
  }
];

// Function to start a service
function startService(service) {
  console.log(`Starting ${service.name} on port ${service.port}...`);
  
  const process = spawn(service.command, service.args);
  
  process.stdout.on('data', (data) => {
    console.log(`[${service.name}] ${data}`);
  });
  
  process.stderr.on('data', (data) => {
    console.error(`[${service.name}] Error: ${data}`);
  });
  
  process.on('close', (code) => {
    console.log(`${service.name} process exited with code ${code}`);
    // Restart the service if it crashes
    setTimeout(() => {
      console.log(`Restarting ${service.name}...`);
      startService(service);
    }, 5000);
  });
  
  return process;
}

// Start all services
const serviceProcesses = services.map(service => startService(service));

// Setup master server endpoints
app.get('/', (req, res) => {
  res.send('Matrix Calculation Backend Server is running');
});

// Endpoint to check the status of all services
app.get('/status', async (req, res) => {
  try {
    const statuses = await Promise.all(services.map(async (service) => {
      try {
        const response = await fetch(`http://localhost:${service.port}/health`);
        return {
          name: service.name,
          port: service.port,
          status: response.ok ? 'UP' : 'DOWN',
          message: response.ok ? await response.text() : 'Service not responding'
        };
      } catch (error) {
        return {
          name: service.name,
          port: service.port,
          status: 'DOWN',
          message: error.message
        };
      }
    }));
    
    res.json({
      masterServer: {
        status: 'UP',
        port: process.env.PORT || 3060
      },
      services: statuses
    });
  } catch (error) {
    res.status(500).json({
      error: 'Error checking service statuses',
      message: error.message
    });
  }
});

// Handle graceful shutdown
function shutdown() {
  console.log('Shutting down all services...');
  
  serviceProcesses.forEach((process, index) => {
    console.log(`Stopping ${services[index].name}...`);
    process.kill();
  });
  
  console.log('All services stopped. Exiting...');
  process.exit(0);
}

// Handle various termination signals
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
process.on('SIGHUP', shutdown);

// Start the master server
const PORT = process.env.PORT || 3060;
app.listen(PORT, () => {
  console.log(`Master server running on port ${PORT}`);
  console.log('All services have been started. Press Ctrl+C to stop all services and exit.');
});
