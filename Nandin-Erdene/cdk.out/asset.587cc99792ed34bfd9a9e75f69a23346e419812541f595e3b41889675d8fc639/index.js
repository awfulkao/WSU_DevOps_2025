// const https = require('https');

// exports.handler = async (event) => {
//     const startTime = Date.now();
//     const url = 'https://www.google.com';
    
//     let isAvailable = false;
//     let latency = null;
//     let statusCode = null;
    
//     try {
//         await new Promise((resolve, reject) => {
//             const req = https.get(url, (res) => {
//                 statusCode = res.statusCode;
//                 isAvailable = res.statusCode >= 200 && res.statusCode < 300;
//                 latency = Date.now() - startTime;
//                 resolve();
//             });
            
//             req.on('error', (err) => {
//                 console.error('Request error:', err);
//                 reject(err);
//             });
            
//             req.setTimeout(5000, () => {
//                 console.error('Request timed out');
//                 req.destroy();
//                 reject(new Error('Timeout'));
//             });
//         });
//     } catch (error) {
//         isAvailable = false;
//         latency = Date.now() - startTime;
//         console.error('Request failed:', error.message);
//     }
    
//     const response = {
//         site: url,
//         isAvailable,
//         latencyMs: latency,
//         statusCode,
//         timestamp: new Date().toISOString()
//     };
    
//     return {
//         statusCode: 200,
//         body: JSON.stringify(response, null, 2),
//     };
// };