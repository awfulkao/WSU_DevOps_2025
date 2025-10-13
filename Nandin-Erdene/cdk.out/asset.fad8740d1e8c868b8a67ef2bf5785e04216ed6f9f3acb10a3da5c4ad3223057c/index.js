const https = require('https');

exports.handler = async (event) => {

    const startTime = Date.now();
    const url = 'www.google.com';

    let isAvailable = false;
    let latency = null;

    try {
    await new Promise((resolve, reject) => {
      const req = https.get(url, (res) => {
        isAvailable = res.statusCode === 200;
        resolve();
      });

      req.on('error', (err) => {
        console.error('Request error:', err);
        reject(err);
      });

      req.setTimeout(5000, () => {
        console.error('Request timed out');
        req.destroy();
        reject(new Error('Timeout'));
      });
    });

    latency = Date.now() - startTime;
  } catch (error) {
    isAvailable = false;
    latency = null;
  }

  const response = {
    site: url,
    isAvailable,
    latencyMs: latency,
    timestamp: new Date().toISOString()
  };

  return {
    statusCode: 200,
    body: JSON.stringify(response, null, 2),
  };
};