const net = require('net');
const c = net.connect(6379, 'redis-broker', () => {
    c.write('PING\r\n');
});
c.on('data', d => {
    console.log('REDIS:', d.toString().trim());
    process.exit(0);
});
c.on('error', e => {
    console.log('FAILED:', e.message);
    process.exit(1);
});
setTimeout(() => { console.log('TIMEOUT'); process.exit(1); }, 5000);
