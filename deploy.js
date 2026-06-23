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
      const fileExists = await sftp.exists(remoteEntryPath);
      if (!fileExists) {
        console.log(`Uploading ${entry}...`);
        await sftp.fastPut(localEntryPath, remoteEntryPath);
      } else {
        console.log(`Skipping ${entry} (already exists)...`);
      }
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

    // Ensure remote admin subdirectory exists
    await sftp.mkdir(`${remotePath}/static/admin`, true);
    await sftp.mkdir(`${remotePath}/admin`, true);
    // Ensure remote backend subdirectory exists
    await sftp.mkdir(`${remotePath}/backend`, true);

    const files = [
      'index.html',
      'v1.html',
      'v1_admin.html',
      'login.html',
      'practice.html',
      'admin/index.html',
      'static/admin/index.html',
      'papers.html',
      'paper-detail.html',
      'tracker.html',
      'mistakes.html',
      'test.html',
      'resources.html',
      'reader.html',
      'css/styles.css',
      'js/app.js',
      'data/papers.json',
      'backend/main.py',
      'backend/paper_triage.py',
      'backend/database.py',
      'backend/models.py',
      'backend/requirements.txt',
      'backend/neetvault.db',
      'backend/sample_paper_10.pdf'
    ];

    for (const file of files) {
      const localFile = path.join(__dirname, file);
      const remoteFile = `${remotePath}/${file}`;
      console.log(`Uploading ${file}...`);
      await sftp.fastPut(localFile, remoteFile);
    }

    // Upload the chapter assets folder recursively
    const localAssetsDir = path.join(__dirname, 'data/assets/chapters');
    const remoteAssetsDir = `${remotePath}/data/assets/chapters`;
    
    console.log('Checking remote chapter assets directory...');
    const assetsDirExists = await sftp.exists(remoteAssetsDir);
    if (!assetsDirExists) {
      await sftp.mkdir(remoteAssetsDir, true);
    }
    
    console.log('Uploading chapter assets recursively...');
    if (fs.existsSync(localAssetsDir)) {
      // await sftp.mkdir(remoteAssetsDir, true);
      // await uploadDirRecursive(localAssetsDir, remoteAssetsDir);
    }

    console.log('Upload complete!');
  } catch (err) {
    console.error('Deployment failed:', err);
  } finally {
    sftp.end();
  }
}

deploy();
