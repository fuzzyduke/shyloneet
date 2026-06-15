const Client = require('ssh2-sftp-client');
const path = require('path');
const fs = require('fs');

const sftp = new Client();
const remotePath = '/opt/sites/shylosoneet';

async function uploadDirRecursive(localDir, remoteDir) {
  const entries = fs.readdirSync(localDir);
  for (const entry of entries) {
    const localEntryPath = path.join(localDir, entry);
    const remoteEntryPath = `${remoteDir}/${entry}`;
    const stat = fs.statSync(localEntryPath);
    if (stat.isDirectory()) {
      const exists = await sftp.exists(remoteEntryPath);
      if (!exists) {
        await sftp.mkdir(remoteEntryPath, true);
      }
      await uploadDirRecursive(localEntryPath, remoteEntryPath);
    } else {
      console.log(`Uploading ${entry}...`);
      await sftp.fastPut(localEntryPath, remoteEntryPath);
    }
  }
}

async function deploy() {
  try {
    console.log('Connecting to VPS...');
    await sftp.connect({
      host: '167.86.84.248',
      port: 22,
      username: 'root',
      password: '2kPJXKNB7U3S'
    });

    console.log(`Ensuring remote directory ${remotePath} exists...`);
    const exists = await sftp.exists(remotePath);
    if (!exists) {
      await sftp.mkdir(remotePath, true);
    }

    const files = [
      'index.html',
      'papers.html',
      'paper-detail.html',
      'tracker.html',
      'mistakes.html',
      'test.html',
      'resources.html',
      'css/styles.css',
      'js/app.js',
      'data/papers.json'
    ];

    for (const file of files) {
      const localFile = path.join(__dirname, file);
      const remoteFile = `${remotePath}/${file}`;
      console.log(`Uploading ${file}...`);
      await sftp.fastPut(localFile, remoteFile);
    }

    /*
    // Upload the papers folder recursively
    const localPapersDir = path.join(__dirname, 'papers');
    const remotePapersDir = `${remotePath}/papers`;
    
    console.log('Checking remote papers directory...');
    const papersDirExists = await sftp.exists(remotePapersDir);
    if (!papersDirExists) {
      await sftp.mkdir(remotePapersDir, true);
    }
    
    console.log('Uploading papers folder recursively...');
    await uploadDirRecursive(localPapersDir, remotePapersDir);
    */

    console.log('Upload complete!');
  } catch (err) {
    console.error('Deployment failed:', err);
  } finally {
    sftp.end();
  }
}

deploy();
