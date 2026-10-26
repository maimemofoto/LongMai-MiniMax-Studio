import assert from 'node:assert/strict';
import fs from 'node:fs';
import EN from '../web/js/h3s_i18n_en.js';
const main = JSON.parse(fs.readFileSync(new URL('../locales/th/main.json', import.meta.url), 'utf8'));
const defs = JSON.parse(fs.readFileSync(new URL('../locales/th/nodeDefs.json', import.meta.url), 'utf8'));
globalThis.window = {};
globalThis.location = { href: 'http://localhost:8188/' };
globalThis.fetch = async (url) => {
  assert.equal(url.pathname, '/i18n');
  return { ok: true, json: async () => ({ th: main }) };
};
const { t, tServer, tDeep, setLangForTests } = await import('../web/js/h3s_i18n.js');
const { HELP_TH } = await import('../web/js/h3s_locale.js');
const { HELP_EN } = await import('../web/js/h3s_help_en.js');
const slots = (s) => [...s.matchAll(/\{\d+\}/g)].map(m => m[0]).sort();
for (const [key, english] of Object.entries(EN)) {
  const thai = main.H3ZeroStudio.ui[key];
  assert.equal(typeof thai, 'string', `Missing Thai: ${key}`);
  assert.ok(thai.trim() || !english.trim(), `Empty Thai: ${key}`);
  assert.deepEqual(slots(thai), slots(english), `Interpolation changed: ${key}`);
  assert.ok(!thai.includes('▁'), `Tokenizer marker: ${key}`);
}
assert.deepEqual(HELP_TH.map(x=>x[0]), HELP_EN.map(x=>x[0]));
for (const name of ['ZL_H3ZeroStudio','ZL_H3Studio']) {
  assert.ok(defs[name].description.match(/[ก-๙]/));
  for (const input of ['project','model','clip','vae','audio_vae','audio']) assert.ok(defs[name].inputs[input].tooltip);
}
setLangForTests('th');
assert.equal(t('Настройки'), 'ตั้งค่า');
assert.equal(t('what each referenced item is and what it contributes'), 'แต่ละสิ่งที่อ้างถึงคืออะไร และให้อะไรกับงาน');
const plain = Object.keys(EN).find(k => EN[k] === 'Processing… keep this window open');
assert.equal(tServer(plain), 'กำลังประมวลผล… อย่าปิดหน้าต่างนี้');
const pattern = Object.keys(EN).find(k => EN[k] === '{0} cards');
assert.equal(tServer(pattern.replace('{0}','7')), '7 การ์ด');
const message = { message: plain, filename:'G:/โมเดล/example.safetensors', prompt:'User <Picture 1> prompt' };
tDeep(message);
assert.equal(message.message, 'กำลังประมวลผล… อย่าปิดหน้าต่างนี้');
assert.equal(message.filename, 'G:/โมเดล/example.safetensors');
assert.equal(message.prompt, 'User <Picture 1> prompt');
setLangForTests('en');
assert.equal(t('Настройки'),'Settings');
assert.equal(tServer(pattern.replace('{0}','7')),'7 cards');
console.log(`Thai locale OK: ${Object.keys(EN).length} source strings, ${HELP_TH.length} help sections, node definitions, placeholders, server messages, English fallback.`);
