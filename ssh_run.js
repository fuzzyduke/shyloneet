const Client = require('ssh2').Client;
const conn = new Client();

const cmd = process.argv[2] || 'lsof -i :8000';

conn.on('ready', () => {
  console.log('Client :: ready');
  conn.exec(cmd, (err, stream) => {
    if (err) throw err;
    stream.on('close', (code, signal) => {
      console.log('Stream :: close :: code: ' + code + ', signal: ' + signal);
      conn.end();
    }).on('data', (data) => {
      console.log('STDOUT: ' + data);
    }).stderr.on('data', (data) => {
      console.log('STDERR: ' + data);
    });
  });
}).connect({
  host: '167.86.84.248',
  port: 22,
  username: 'root',
  password: '2kPJXKNB7U3S'
});
