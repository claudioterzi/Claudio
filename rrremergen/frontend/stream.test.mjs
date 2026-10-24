import { test } from 'node:test';
import assert from 'node:assert/strict';
import { compositionEvents } from './stream.js';

function response(chunks) {
  return new Response(new ReadableStream({ start(controller) {
    for (const chunk of chunks) controller.enqueue(new TextEncoder().encode(chunk));
    controller.close();
  } }));
}
const collect = async r => { const out = []; for await (const e of compositionEvents(r)) out.push(e); return out; };

test('split SSE frames and final frame without newline', async () => {
  const output = await collect(response(['data: {"type":"stage_', 'progress","stage":"pm"}\r\n\r\n',
    'data: {"type":"completion","app":{"title":"Attività"}}']));
  assert.equal(output.length, 2);
  assert.equal(output[1].app.title, 'Attività');
});
test('backend error remains visible', async () => {
  await assert.rejects(collect(response(['data: {"type":"error","message":"Provider fallito"}\n\n'])), /Provider fallito/);
});
test('EOF without completion is a failure', async () => {
  await assert.rejects(collect(response(['data: {"type":"stage_progress"}\n\n'])), /prima del completamento/);
});
test('malformed JSON and HTTP failures are rejected', async () => {
  await assert.rejects(collect(response(['data: nope\n\n'])), SyntaxError);
  await assert.rejects(collect(new Response('error', { status: 500 })), /500/);
});
