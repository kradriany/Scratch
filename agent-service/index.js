const axios = require('axios');

async function pollStatus() {
  try {
    const res = await axios.get('http://api-emulator:3000/status');
    console.log('Emulator status:', res.data);
  } catch (err) {
    console.error('Error polling emulator:', err.message);
  }
}

setInterval(pollStatus, 5000);
pollStatus();
