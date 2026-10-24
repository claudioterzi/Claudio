/* R3 iPhone LAN decryptor: © Claudio Terzi 2026.
   The URL fragment contains a random bearer key. No credentials go to the NAS server.
   Do not expose sensitive facts via console logs or other resources. */
(function(){
  'use strict';
  const status=document.getElementById('unlockStatus');
  const lock=document.getElementById('unlockView');
  const root=document.getElementById('portalRoot');
  function b64bytes(base64){
    const b=atob(String(base64).replace(/-/g,'+').replace(/_/g,'/'));
    const out=new Uint8Array(b.length);
    for(let i=0;i<b.length;i++) out[i]=b.charCodeAt(i);
    return out;
  }
  function fail(message){
    status.textContent=message;
    lock.hidden=false;
    root.hidden=true;
  }
  async function unlock(){
    try{
      const hash=new URLSearchParams(location.hash.replace(/^#/,''));
      const encoded=hash.get('key') || (function(){try{return sessionStorage.getItem('r3.book.session.key.v1') || sessionStorage.getItem('r3.book.pending.key.v1') || '';}catch(_){return '';}})();
      if(!encoded || !/^[A-Za-z0-9_-]{43}$/.test(encoded)){
        fail('Manca la chiave nel collegamento. Apri il link completo che hai ricevuto in ChatGPT, incluso il simbolo #.');
        return;
      }
      if(!window.nacl || !window.nacl.secretbox){
        fail('La libreria locale di cifratura non è disponibile.');
        return;
      }
      status.textContent='Carico e verifico la copia cifrata…';
      const response=await fetch('./payload.json',{cache:'no-store'});
      if(!response.ok) throw Error('Il NAS non ha restituito la copia cifrata ('+response.status+').');
      const packet=await response.json();
      if(packet.v!==1 || packet.alg!=='XSalsa20-Poly1305')throw Error('Formato archivio non riconosciuto.');
      const key=b64bytes(encoded);
      const clear=nacl.secretbox.open(b64bytes(packet.box),b64bytes(packet.nonce),key);
      key.fill(0);
      if(!clear)throw Error('Il link privato non corrisponde a questa copia dell’archivio.');
      const uncompressed=packet.compression==='gzip' ? (await (async()=>{if(typeof DecompressionStream!=='function')throw Error('Browser senza decompressione gzip.');return new Uint8Array(await new Response(new Blob([clear]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());})()) : clear;
      const payload=JSON.parse(new TextDecoder().decode(uncompressed));
      clear.fill(0);if(uncompressed!==clear)uncompressed.fill(0);
      if(payload.schema!=='R3_IPHONE_ENCRYPTED_BUNDLE_V1'
        || !Array.isArray(payload.registry?.records)
        || !Array.isArray(payload.cubo?.nodes)
        || !Array.isArray(payload.graphify?.nodes)
        || payload.registry.records.length!==64
        || payload.graphify.nodes.length!==1010){
        throw Error('Contenuto dell’archivio non integro.');
      }
      window.R3_IDEA_REGISTRY=payload.registry;
      window.CUBO_OPERE_DATA=payload.cubo;
      window.__r3GraphifyPending=payload.graphify;
      window.__r3SecureMobile=true;try{sessionStorage.setItem('r3.book.session.key.v1',encoded);sessionStorage.removeItem('r3.book.pending.key.v1')}catch(_){}
      lock.hidden=true;
      root.hidden=false;
      const script=document.createElement('script');
      script.src='app.js';
      script.onerror=()=>{root.hidden=true;lock.hidden=false;fail('Impossibile avviare l’interfaccia. Controlla i file della cartella web.');};
      script.onload=()=>{
        const count=document.getElementById('statIdeas')?.textContent;
        if(count!=='38')fail('Il catalogo non ha completato il caricamento.');
      };
      document.body.appendChild(script);
    }catch(err){
      fail(err instanceof Error?err.message:'Non sono riuscito ad aprire questa copia del Libro.');
    }
  }
  unlock();
})();
