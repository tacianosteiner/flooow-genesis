"""Include legacy-encoded text discovery; preserve original source bytes."""
import json
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
def main():
    p=O/'search-inventory.json';d=json.loads(p.read_text(encoding='utf-8'));results=[]
    for item in d['files']:
        if item['kind']!='NON_UTF8_NO_TEXT_AUTHORITY' or Path(item['path']).suffix.lower() not in ['.md','.txt','.json','.sql','.py','.c','.h','.kt']:continue
        raw=(R/item['path']).read_bytes()
        if raw.startswith((b'\xff\xfe',b'\xfe\xff')):text=raw.decode('utf-16');encoding='UTF16_BOM'
        else:
            try:text=raw.decode('cp1252');encoding='CP1252_DISCOVERY_ONLY'
            except UnicodeError:text=raw.decode('latin1');encoding='LATIN1_DISCOVERY_ONLY'
        lowered=text.casefold();relevant=any(t in item['path'].casefold() or t in lowered for t in ['0090','r5n','credential_inheritance'])
        item.update(kind='LEGACY_TEXT_DISCOVERY',encoding=encoding,relevant=relevant)
        terms=[t for t in d['terms'] if t.casefold() in lowered]
        if relevant:
            for t in terms:
                if item['path'] not in d['coverage'][t]:d['coverage'][t].append(item['path'])
        hits=[]
        for i,line in enumerate(text.splitlines()):
            low=line.casefold()
            if ('inherit' in low and 'credential' in low) or any(t in low for t in ['private descriptor','public manifest','manifest copy']) or ('postmaster' in low and any(t in low for t in ['credential','custod','endpoint','key'])):hits.append(dict(line=i+1,text=line))
        results.append(dict(path=item['path'],encoding=encoding,relevant=relevant,term_hits=terms,semantic_hits=hits,authority_warning='Decoding/read-only discovery does not promote runtime log or implementation into semantic authority'))
    d['total_relevant']=sum(x.get('relevant',False) for x in d['files']);d['search_scope']='All8883 tracked/pre-existing untracked files inventoried; UTF8 text plus BOM-aware UTF16 and CP1252/Latin1 legacy text discovery. All32 exact terms, semantic line conjunctions, full referenced contract/JSON selections. New gate excluded. No keyword-absence inference.'
    p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (O/'legacy-text-search.json').write_text(json.dumps(dict(files=results,count=len(results),source_bytes_unchanged=True),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(legacy_text_files=len(results),legacy_semantic_hits=sum(len(x['semantic_hits']) for x in results))))
if __name__=='__main__':main()
