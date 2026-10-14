"""Build a reader/index from the preserved integral edition, without changing it."""
from pathlib import Path
from html import escape, unescape
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'public'
SOURCE=PUBLIC/'libro-integrale.html'
DEST=PUBLIC/'libro'
SOURCE_COMMIT='17cac359250b8af1850ac22cf21944fa0448da78'
BASELINE_GIT_CONTENT_SHA256='3060e9576b1cbc6e4c84732d8f1c2c79d6b5865cf833fbe6ff4ef95177188b85'

def plain(value):
    return re.sub(r'\s+',' ',unescape(re.sub('<[^>]*>',' ',value))).strip()
def sha(value): return hashlib.sha256(value).hexdigest()

def build():
    raw=SOURCE.read_bytes()
    normalized_sha=sha(raw.replace(b'\r\n',b'\n'))
    preserved_baseline=normalized_sha==BASELINE_GIT_CONTENT_SHA256
    original=raw.decode('utf-8').replace('\r\n','\n')
    start=original.index('<div class="copertina">')
    end=original.rindex('</div>\n</body>')
    body=original[start:end]
    headings=list(re.finditer(r'<h1 class="(?:parte|capitolo)">([^<]+)</h1>',body))
    assert len(headings)==12, 'Expected four parts and eight families.'
    DEST.mkdir(exist_ok=True)
    metadata=[]; perfumes=[]; provenance=[]
    boundaries=[(0,'Introduzione e avvertenze','introduzione')]
    catalogue_start=next(match.start() for match in headings if 'Parte IV' in match.group(1))
    for match in headings:
        if 'Parte IV' in match.group(1): continue
        title=plain(match.group(1))
        identity='capitolo-'+re.search(r'Capitolo (\d+)',title).group(1) if title.startswith('Capitolo') else 'parte-'+['I','II','III'].index(re.search(r'Parte (I+) ',title).group(1)).__str__()
        boundaries.append((catalogue_start if identity=='capitolo-1' else match.start(),title,identity))
    for i,(offset,title,identity) in enumerate(boundaries):
        stop=boundaries[i+1][0] if i+1<len(boundaries) else len(body)
        fragment=body[offset:stop]
        ids=re.findall(r'\bid="([^\"]+)"',fragment)
        chapter_perfumes=list(re.finditer(r'<div class="scheda" id="profumo-(\d+)">',fragment))
        for index,match in enumerate(chapter_perfumes):
            perfume_body=fragment[match.start():chapter_perfumes[index+1].start() if index+1<len(chapter_perfumes) else len(fragment)]
            name=re.search(r'<h3>(.*?)</h3>',perfume_body,re.S)
            concept=re.search(r'<p class="concept">(.*?)</p>',perfume_body,re.S)
            perfumes.append({'id':'profumo-'+match.group(1),'n':int(match.group(1)),'title':plain(name.group(1)),'chapter':identity,'family':title.split(' — ',1)[-1],'summary':plain(concept.group(1)) if concept else ''})
        adjusted=re.sub(r'<(/?)h2\b',r'<\1h3',fragment)
        adjusted=re.sub(r'<(/?)h1\b',r'<\1h2',adjusted)
        filename=identity+'.html'
        data=adjusted.encode('utf-8')
        (DEST/filename).write_bytes(data)
        metadata.append({'id':identity,'title':title,'url':'libro/'+filename,'anchors':ids,'perfumes':len(chapter_perfumes)})
        provenance.append({'file':'public/libro/'+filename,'source_start_character':start+offset,'source_end_character':start+stop,'raw_fragment_sha256':sha(fragment.encode('utf-8')),'derived_fragment_sha256':sha(data),'heading_adjustment':'h1 to h2, h2 to h3 for chapter view; integral edition unchanged'})
    assert len(perfumes)==400 and [p['n'] for p in perfumes]==list(range(1,401))
    (DEST/'indice.json').write_text(json.dumps({'chapters':metadata,'perfumes':perfumes},ensure_ascii=False,separators=(',',':')),encoding='utf-8',newline='\n')
    css=re.search(r'<style>(.*?)</style>',original,re.S).group(1)
    (PUBLIC/'libro-classico.css').write_text(css,encoding='utf-8',newline='\n')
    svg=re.search(r'<svg width="0".*?</svg>',original,re.S).group(0)
    toc=''.join('<li><a href="#'+escape(item['id'])+'">'+escape(item['title'])+'</a></li>' for item in metadata)
    shell='''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Il Libro dei Parfums 400 · Indice e lettura</title>
<meta name="description" content="Cerca tra 400 profumi e leggi storia, sapere e famiglie del Libro Terzi, un capitolo alla volta.">
<link rel="canonical" href="https://claudio-ebon.vercel.app/libro.html">
<link rel="stylesheet" href="mouillette.css"><link rel="stylesheet" href="libro-classico.css"><link rel="stylesheet" href="libro-reader.css">
<script src="mouillette.js" defer></script><script src="libro-reader.js" defer></script></head><body>
<script src="soglia.js"></script><script src="nav.js"></script>'''+svg+'''
<main class="book-reader"><header><p>TERZI PARFUMS · CLAUDIO TERZI</p><h1>Il Libro dei Parfums 400</h1>
<p>Storia, sapere, organo e quattrocento creazioni. Scegli un capitolo o cerca un profumo.</p>
<nav class="olf-toolbar" aria-label="Libro e lettura"><a href="libro-integrale.html">Versione integrale originale e stampa</a><a href="parfums.html">Catalogo dei profumi</a><a href="magazine.html">Magazine mensile</a><a href="#book-content">Vai al capitolo aperto</a></nav></header>
<div class="book-layout"><aside class="book-index"><details id="book-index-toggle" open><summary>Indice e ricerca nel libro</summary><h2>Indice</h2><ol>'''+toc+'''</ol>
<label for="book-search">Cerca per nome, numero, famiglia o descrizione</label><input id="book-search" type="search" placeholder="Es. Lettre de Midi, Agrumata, 37">
<p id="book-results-count" role="status" aria-live="polite"></p><ul id="book-results"></ul><button id="book-more" type="button" hidden>Mostra altri 20 profumi</button></details></aside>
<section class="book-reading" aria-label="Capitolo aperto"><div class="book-tools"><button id="book-index-open" type="button" aria-controls="book-index-toggle">Indice e ricerca</button><button type="button" data-olf-print="chapter">Stampa il capitolo aperto</button></div><p id="book-status" role="status" aria-live="polite"></p><button id="book-retry" type="button" hidden>Riprova il caricamento</button><div id="book-content" class="libro" tabindex="-1"><p>Apri un capitolo dall’indice. Le ricette restano quelle dell’edizione integrale.</p></div><nav class="book-chapter-nav" aria-label="Altri capitoli"><a id="book-prev" hidden>Capitolo precedente</a><a id="book-next" hidden>Capitolo successivo</a></nav></section></div>
<noscript><p>Per consultare il libro senza JavaScript apri la <a href="libro-integrale.html">versione integrale originale</a>.</p></noscript>
<footer><p>Claudio Terzi · C.Terzi · Ricette dell’edizione integrale.</p></footer></main></body></html>'''
    (PUBLIC/'libro.html').write_text(shell,encoding='utf-8',newline='\n')
    (DEST/'provenienza.json').write_text(json.dumps({'source_file':'public/libro-integrale.html','source_commit':SOURCE_COMMIT if preserved_baseline else None,'source_state':'PRESERVED_BASELINE' if preserved_baseline else 'GENERATED_CANDIDATE','source_sha256':sha(raw),'source_bytes':len(raw),'git_blob_sha256':normalized_sha,'git_blob_digest_note':'SHA256 of Git content after CRLF-to-LF normalization, not a Git object ID; source_sha256 is the exact checkout-byte digest. For a future generated candidate, source_commit remains null until its provenance is reviewed.','source_offsets':'Characters after CRLF-to-LF normalization, not byte offsets','perfumes':400,'chapters':provenance},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    assert SOURCE.read_bytes()==raw, 'Integral edition must remain unchanged.'
    print(json.dumps({'source_sha256':sha(raw),'source_bytes':len(raw),'reader_bytes':(PUBLIC/'libro.html').stat().st_size,'index_bytes':(DEST/'indice.json').stat().st_size,'chapters':len(metadata),'perfumes':400}))

if __name__=='__main__': build()
