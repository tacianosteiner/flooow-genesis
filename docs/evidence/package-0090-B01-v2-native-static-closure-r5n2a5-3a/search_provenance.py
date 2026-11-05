"""Read-only repository search; writes only this gate's evidence."""
import hashlib,json,re,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
TERMS=['POSTMASTER','credential_inheritance','credential inheritance','inherit credential','inherited credential','credential descriptor','private descriptor','manifest','public manifest','manifest copy','credential copy','credential material','secret material','credential identity','credential authority','credential subject','authority transition','authority inheritance','authority delegation','authority transfer','custody','owner','reader','writer','parent_identity','generation','restart','replacement','substitution','requalification','revocation','endpoint manifest']
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):(O/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
    branch=git('branch','--show-current');head=git('rev-parse','HEAD')
    assert branch=='checkpoint/package-0090-cloud-handoff' and head=='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb'
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    tracked=git('ls-files').splitlines();untracked=git('ls-files','--others','--exclude-standard').splitlines()
    prefix=O.relative_to(R).as_posix()+'/'
    # Search script is the first newly created gate artifact, excluded from baseline.
    original=[p for p in untracked if not p.startswith(prefix)]
    assert len(original)==401,len(original)
    paths=sorted(set(tracked+original));inventory=[];hits=[];coverage={t:[] for t in TERMS};refs=[]
    relevant=re.compile(r'0090|package.?0090|R5N|credential_inheritance',re.I)
    tight=re.compile(r'credential[_ -]inherit|inherit\w*.{0,60}credential|credential.{0,60}inherit|private descriptor|public manifest|manifest copy|POSTMASTER.{0,140}(credential|custod|endpoint|key)|(?:credential|custod|endpoint|key).{0,140}POSTMASTER',re.I)
    frozen={p:sha(R/p) for p in paths}
    put('baseline-freeze.json',dict(branch=branch,head=head,tracked_paths=tracked,untracked_before_paths=original,UNTRACKED_BEFORE=401,source_sha256=frozen))
    for name in paths:
        p=R/name
        try:text=p.read_text(encoding='utf-8-sig')
        except (UnicodeError,OSError):inventory.append(dict(path=name,kind='NON_UTF8_NO_TEXT_AUTHORITY',sha256=frozen[name]));continue
        lowered=text.casefold();path_lower=name.casefold()
        is_relevant=any(t in path_lower or t in lowered for t in ['0090','r5n','credential_inheritance']);inventory.append(dict(path=name,kind='TEXT',relevant=is_relevant,sha256=frozen[name]))
        if not is_relevant:continue
        for term in TERMS:
            if term.casefold() in lowered:coverage[term].append(name)
        lines=text.splitlines()
        for i,line in enumerate(lines):
            lowerline=line.casefold()
            semantic_hit=(('inherit' in lowerline and 'credential' in lowerline) or any(t in lowerline for t in ['private descriptor','public manifest','manifest copy']) or ('postmaster' in lowerline and any(t in lowerline for t in ['credential','custod','endpoint','key'])))
            if semantic_hit:hits.append(dict(path=name,line=i+1,text=line,context_before=lines[max(0,i-2):i],context_after=lines[i+1:i+3],authority_warning='Source text requires authority adjudication; code/results/repeated claims are not automatically canonical'))
        for target in re.findall(r'(?:docs|scripts|src)/[\w./-]+\.(?:json|md|sql|py|kt)',text):
            if (R/target).is_file():refs.append(dict(from_path=name,to_path=target,in_inventory=target in frozen))
    put('search-inventory.json',dict(files=inventory,tracked_count=len(tracked),untracked_before=401,search_scope='Every tracked and pre-existing untracked file; all UTF8 text searched for relevance by pathname and content. New gate excluded, binary files retained in inventory. Exact term search supplemented by semantic line conjunctions and manual full-contract/JSON pointer reading.',terms=TERMS,coverage=coverage,total_relevant=sum(x.get('relevant',False) for x in inventory),transitive_existing_path_references=refs,unresolved_existing_references=[x for x in refs if not x['in_inventory']]))
    put('semantic-search-passages.json',dict(hits=hits,count=len(hits),semantic_search='Casefolded line conjunctions: inherit+credential; private descriptor; public manifest; manifest copy; POSTMASTER plus credential/custod/endpoint/key. Superset of bounded-distance regex, retaining all contexts.',not_proof_of_absence='Search hits are discovery only; outcome must follow source relationships and exact semantics.'))
    print(json.dumps(dict(branch=branch,head=head,untracked_before=401,files=len(paths),relevant=sum(x.get('relevant',False) for x in inventory),passages=len(hits))))
if __name__=='__main__':main()
