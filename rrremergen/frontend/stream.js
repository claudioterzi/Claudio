/** Consume SSE with one required terminal outcome and visible backend errors. */
export async function* compositionEvents(response) {
  if (!response.ok || !response.body) throw new Error(`Composizione non disponibile (${response.status})`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let completed = false;
  const parse = block => {
    const data = block.split(/\r?\n/).filter(line => line.startsWith('data:'))
      .map(line => line.slice(5).trimStart()).join('\n');
    return data ? JSON.parse(data) : null;
  };
  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
      const blocks = buffer.split(/\r?\n\r?\n/);
      buffer = blocks.pop();
      if (done && buffer.trim()) { blocks.push(buffer); buffer = ''; }
      for (const block of blocks) {
        const event = parse(block);
        if (!event) continue;
        if (event.type === 'error') throw new Error(event.message || 'Generazione interrotta');
        if (event.type === 'completion') completed = true;
        yield event;
      }
      if (done) break;
    }
    if (!completed) throw new Error('Flusso interrotto prima del completamento');
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
