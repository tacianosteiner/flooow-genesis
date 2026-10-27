"""Derive complete non-bootstrap function profiles from source declarations."""
import json
import package_0090_reachable_v2 as e
OUT=e.OUT

def prepare(r):
 identity=json.loads((OUT/'function-identity-v6.json').read_text());acl=json.loads((OUT/'effective-acl-v6.json').read_text());profiles=[]
 for f in identity['canonical_functions']+identity['native_functions']:
  ast=f['source_AST'];opts={x['DefElem']['defname']:x['DefElem'].get('arg') for x in ast['options']};params=[p['FunctionParameter'] for p in ast.get('parameters',[])];modes={'FUNC_PARAM_DEFAULT':'i','FUNC_PARAM_IN':'i','FUNC_PARAM_OUT':'o','FUNC_PARAM_TABLE':'t','FUNC_PARAM_INOUT':'b','FUNC_PARAM_VARIADIC':'v'}
  alltypes=[r.typename(p['argType']) for p in params];argmodes=[modes[p.get('mode','FUNC_PARAM_DEFAULT')] for p in params];args=[t for t,m in zip(alltypes,argmodes) if m not in ['o','t']];hasout=any(m in ['o','t','b'] for m in argmodes);names=[p.get('name','') for p in params];language=opts['language']['String']['sval'].lower();name=f['signature'].split('(')[0];owner=f['owner'];body=f.get('body',f.get('symbol'));settings=[]
  for o in ast['options']:
   d=o['DefElem']
   if d['defname']=='set':
    setting=d['arg']['VariableSetStmt'];settings.append(setting['name']+'='+', '.join(v['A_Const']['sval']['sval'] for v in setting['args']))
  parallel={'safe':'s','restricted':'r','unsafe':'u'}[opts.get('parallel',{}).get('String',{}).get('sval','unsafe')];vol={'stable':'s','immutable':'i','volatile':'v'}[opts.get('volatility',{}).get('String',{}).get('sval','volatile')];setof=bool(ast['returnType'].get('setof'))
  raw_acl=None
  if language=='plpgsql':
   grants={owner:False,**acl['source_function_direct_grants'][name]};raw_acl=sorted([dict(grantee=role,privilege='EXECUTE',grantable=go,grantor=owner) for role,go in grants.items()],key=lambda x:x['grantee'])
  elif name.startswith('offline_crypto.'):
   grantee='flooow_offline_verification_owner' if name.endswith('canonical_spki_ed25519_verify') else 'flooow_offline_readiness_owner';raw_acl=sorted([dict(grantee=role,privilege='EXECUTE',grantable=False,grantor='postgres') for role in ['postgres',grantee]],key=lambda x:x['grantee'])
  profiles.append(dict(signature=f['signature'],owner=owner,language=language,args=args,allargs=alltypes if hasout else None,argmodes=argmodes if hasout else None,argnames=names if any(names) else None,result=r.typename(ast['returnType']),returns_set=setof,security_definer=opts.get('security',{}).get('Boolean',{}).get('boolval',False),strict=opts.get('strict',{}).get('Boolean',{}).get('boolval',False),volatile=vol,parallel=parallel,leakproof=False,config=settings or None,source=body,library=f.get('native_library'),support_oid=0,cost=1 if language=='c' else 100,rows=1000 if setof else 0,kind='f',defaults_SQL=None,raw_acl=raw_acl))
 identity['source_profiles']=profiles;e.save('function-identity-v6.json',identity);print('Source/native profiles',len(profiles))
if __name__=='__main__':
 import sys
 from pathlib import Path
 sys.path.insert(0,str(Path.home()/'.codex/tmp/package0090-pglast-8.5'));from pglast.parser import parse_sql_json
 prepare(e.Resolver(parse_sql_json))
