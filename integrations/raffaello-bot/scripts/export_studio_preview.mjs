// Public visual preview only: never export database rows, initData, tokens or env values.
import { copyFile, mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const assets = resolve(root, 'integrations/raffaello-bot/bot/studio_static');
const output = resolve(root, 'output/raffaello-studio-preview');
const studio = resolve(output, 'studio');
await mkdir(studio, { recursive: true });
for (const filename of ['index.html', 'studio.css', 'studio.js']) {
  await copyFile(resolve(assets, filename), resolve(studio, filename));
}
await copyFile(resolve(assets, 'index.html'), resolve(output, 'index.html'));
await copyFile(resolve(root, 'public/musica-data.js'), resolve(studio, 'musica-data.js'));
await writeFile(resolve(studio, 'config'), JSON.stringify({
  bot_username: 'ProtocolloRossoBot',
  bot_url: 'https://t.me/ProtocolloRossoBot',
  generation_mode: 'assisted',
  capabilities: { requests: false, lyrics_generation: false, audio_generation: false,
    result_delivery: false, owner_controls: false, personal_voice: false },
  preview: true
}), 'utf8');
console.log('Public Studio preview built; private operations disabled.');
