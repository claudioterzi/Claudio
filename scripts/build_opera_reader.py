"""Preserve the canonical corpus and build per-document files for lazy reading."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
def build():
    corpus=json.loads((ROOT/'public/opera-corpus.json').read_text(encoding='utf-8'))
    if not isinstance(corpus,list) or not corpus:
        raise ValueError('Opera corpus must contain at least one document')
    destination=ROOT/'public/opera';destination.mkdir(exist_ok=True)
    records=[]
    for index,doc in enumerate(corpus):
        data=doc['html'].encode('utf-8');digest=hashlib.sha256(data).hexdigest()
        name=f'document-{index:03d}-{digest[:16]}.html'
        (destination/name).write_bytes(data)
        records.append({k:v for k,v in doc.items() if k!='html'}|{'src':'opera/'+name,'sha256':digest,'bytes':len(data)})
    page=ROOT/'public/opera.html'
    template=ROOT/'scripts/opera_reader_template.html'
    text=template.read_text(encoding='utf-8')
    metadata=json.dumps(records,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    first=json.dumps(corpus[0],ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    if any(text.count(marker)!=1 for marker in ('__OPERA_DOCS_JSON__','__OPERA_FIRST_DOC_JSON__','__OPERA_COUNT__')):
        raise ValueError('Reader template placeholders not found exactly once')
    text=text.replace('__OPERA_DOCS_JSON__',metadata).replace('__OPERA_FIRST_DOC_JSON__',first).replace('__OPERA_COUNT__',str(len(records)))
    page.write_text(text,encoding='utf-8',newline='\n')
    (destination/'manifest.json').write_text(json.dumps({'schema':'OPERA-LAZY/1','source_corpus':'../opera-corpus.json','documents':records,'html_total_bytes':sum(x['bytes'] for x in records),'source_corpus_sha256':hashlib.sha256((ROOT/'public/opera-corpus.json').read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'documents':len(records),'html_bytes':page.stat().st_size,'initial_document_bytes':records[0]['bytes'],'corpus_preserved':True}))
if __name__=='__main__':build()
