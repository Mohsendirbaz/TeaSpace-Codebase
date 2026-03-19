const fs = require('fs');
const path = require('path');

const target = path.join(process.cwd(), 'public', 'Original');

try {
  const stats = fs.lstatSync(target);
  if (stats.isSymbolicLink() || stats.isFile()) {
    fs.unlinkSync(target);
  } else if (!stats.isDirectory()) {
    fs.rmSync(target, { recursive: true, force: true });
  }
} catch (error) {
  if (error.code !== 'ENOENT') {
    console.warn(`Unable to inspect ${target}: ${error.message}`);
  }
}

fs.mkdirSync(target, { recursive: true });
console.log(`Prepared ${target}`);
