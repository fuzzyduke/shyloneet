const { Client } = require('ssh2');

const conn = new Client();

conn.on('ready', () => {
    conn.exec('cat /etc/nginx/sites-available/buddies.valhallala.com', (err, stream) => {
        if (err) throw err;
        stream.on('close', (code, signal) => {
            conn.end();
        }).on('data', (data) => {
            console.log('STDOUT:\n' + data);
        }).stderr.on('data', (data) => {
            console.error('STDERR:\n' + data);
        });
    });
}).connect({
    host: '167.86.84.248',
    port: 22,
    username: 'root',
    password: '2kPJXKNB7U3S'
});
