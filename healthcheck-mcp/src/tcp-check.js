const net = require('net');

function checkTcpPort(host, port, timeout = 1000) {
    return new Promise((resolve, reject) => {
        const socket = new net.Socket();

        const timer = setTimeout(() => {
            socket.destroy();
            reject(new Error(`TCP connection to ${host}:${port} timed out after ${timeout}ms`));
        }, timeout);

        socket.connect(port, host, () => {
            clearTimeout(timer);
            socket.end();
            resolve(true);
        });

        socket.on('error', (err) => {
            clearTimeout(timer);
            socket.destroy();
            reject(new Error(`TCP connection to ${host}:${port} failed: ${err.message}`));
        });
    });
}

module.exports = { checkTcpPort };
