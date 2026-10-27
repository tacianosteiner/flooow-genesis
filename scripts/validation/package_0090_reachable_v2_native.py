"""Freeze native ELF/provider bindings from the approved image, before targets."""
import json,re
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT,save

def prepare():
 binaries=['/usr/lib/postgresql/18/bin/postgres','/usr/lib/postgresql/18/lib/plpgsql.so','/usr/lib/postgresql/18/lib/pgcrypto.so'];paths=set(binaries);ldd={}
 for binary in binaries:
  data=q.command(['docker','run','--rm','--network','none','--read-only','--entrypoint','ldd',q.IMAGE,binary]).stdout.decode();ldd[binary]=re.sub(r'\s*\(0x[0-9a-fA-F]+\)','',data);paths.update(re.findall(r'(?:=>\s*)?(/[^\s(]+)',data))
 paths=sorted(paths);hashes=q.command(['docker','run','--rm','--network','none','--read-only','--entrypoint','sha256sum',q.IMAGE,*paths]).stdout.decode().splitlines();entries=[]
 for line in hashes:
  digest,path=line.split(None,1);entries.append(dict(path=path.strip(),sha256=digest,owner_rule='root UID/GID; resolved regular file not writable by group/other; managed process identity binds loaded provider epoch'))
 locale_paths=q.command(['docker','run','--rm','--network','none','--read-only','--entrypoint','find',q.IMAGE,'/usr/lib/locale','-maxdepth','3','-type','f']).stdout.decode().splitlines()
 locale_paths=[p for p in locale_paths if 'locale-archive'in p or '/en_US.'in p]
 locale_data=[]
 if locale_paths:
  data=q.command(['docker','run','--rm','--network','none','--read-only','--entrypoint','sha256sum',q.IMAGE,*locale_paths]).stdout.decode().splitlines()
  locale_data=[dict(sha256=line.split()[0],path=line.split(None,1)[1]) for line in data]
 source=q.ROOT/'applications/marketplace-operations-persistence-postgres/native/flooow_offline_mac32'
 save('native-provider-identities.json',dict(image=q.IMAGE,ELF_files=entries,locale_data_files=locale_data,ldd=ldd,custom_module=dict(path='/usr/lib/postgresql/18/lib/flooow_offline_mac32.so',sha256='5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5',source_files={p.relative_to(q.ROOT).as_posix():q.sha(p.read_bytes()) for p in source.iterdir() if p.is_file()},build='Approved image make with_llvm=no; fresh foundation rebuild must reproduce exact module bytes'),kernel_boundary='vDSO and kernel/boot/timens identities belong to HOST_PLATFORM independent anchor rules; never replace with an assumed zero or historical process proof',libc_version=(OUT/'provider/libc-version.txt').read_text().strip(),independent=True))
 print('Native provider files',len(entries))
if __name__=='__main__':prepare()
