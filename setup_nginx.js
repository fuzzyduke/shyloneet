const Client = require('ssh2-sftp-client');
const { Client: SSHClient } = require('ssh2');

const sftp = new Client();
const nginxConfig = `server {
    listen 80;
    listen [::]:80;
    listen 443 ssl;
    listen [::]:443 ssl;

    server_name shylosoneet.valhallala.com;

    ssl_certificate /etc/nginx/ssl/nginx.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /opt/sites/shylosoneet;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}`;

async function setup() {
    try {
        console.log('Connecting SFTP...');
        await sftp.connect({
            host: '167.86.84.248',
            port: 22,
            username: 'root',
            password: '2kPJXKNB7U3S'
        });

        console.log('Uploading Nginx config...');
        const buffer = Buffer.from(nginxConfig, 'utf8');
        await sftp.put(buffer, '/etc/nginx/sites-available/shylosoneet.valhallala.com');
        await sftp.end();
        console.log('Upload complete. Running commands...');

        const conn = new SSHClient();
        conn.on('ready', () => {
            const commands = [
                'nginx -t && systemctl reload nginx'
            ];
            conn.exec(commands.join(' && '), (err, stream) => {
                if (err) throw err;
                stream.on('close', (code, signal) => {
                    console.log('Stream :: close :: code: ' + code);
                    conn.end();
                }).on('data', (data) => {
                    console.log('STDOUT: ' + data);
                }).stderr.on('data', (data) => {
                    console.error('STDERR: ' + data);
                });
            });
        }).connect({
            host: '167.86.84.248',
            port: 22,
            username: 'root',
            password: '2kPJXKNB7U3S'
        });

    } catch (err) {
        console.error(err);
    }
}

setup();
