const fs = require('fs');
const code1 = fs.readFileSync('telegram_worker.js').toString('base64');
const code2 = fs.readFileSync('src/services/telegram.js').toString('base64');
console.log(`node -e "require('fs').writeFileSync('telegram_worker.js', Buffer.from('${code1}', 'base64'));"`);
console.log(`node -e "require('fs').writeFileSync('src/services/telegram.js', Buffer.from('${code2}', 'base64'));"`);
