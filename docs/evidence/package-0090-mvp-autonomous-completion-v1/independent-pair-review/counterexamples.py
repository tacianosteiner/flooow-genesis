import sys,importlib.util,json,hashlib,struct
sys.dont_write_bytecode=True
p=sys.argv[1]
spec=importlib.util.spec_from_file_location('reviewed_pair',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def ref(n):return (1,bytes([n]))
def target(n):return (tuple(ref(x) for x in (1,2,n,4,5,6,7)),1,10,20,(1,2,n),b'reader')
def expect(role):return dict(target=target(3),observer=tuple(ref(x+role*20) for x in (1,2,3,4,5)),origin=ref(90+role),domain=tuple(ref(x+100) for x in range(9)),lease=(100,1000,800,950),root_interval=(200,210),sources=tuple((tuple(ref(140+i*4+j) for j in range(4)),bytes([i+1])*32) for i in range(8)),population=ref(190),members=(target(3),))
class W:
 def __init__(self):self.b=bytearray()
 def u(self,x):self.b+=struct.pack('>I',x)
 def q(self,x):self.b+=struct.pack('>Q',x)
 def r(self,x):self.u(x[0]);self.u(len(x[1]));self.b+=x[1]
 def name(self,x):self.u(len(x));self.b+=x
 def t(self,x):
  for r in x[0]:self.r(r)
  for q in x[1:4]:self.q(q)
  for u in x[4]:self.u(u)
  self.name(x[5])
 def src(self,s):
  for r in s[0]:self.r(r)
  self.b+=s[1]
def frame(role,e,ordinal=0):
 w=W();w.b+=b'S03OBSE2'
 for x in (2,role,1,0):w.u(x)
 w.q(0)
 for _ in range(9):w.u(1)
 w.b+=m.CONSUMER;w.t(e['target'])
 for r in e['observer']:w.r(r)
 w.r(e['origin'])
 for r in e['domain']:w.r(r)
 for q in (300,310)+e['root_interval']+e['lease']:w.q(q)
 w.u(1)
 for q in (250,260,950):w.q(q)
 for s in e['sources']:w.src(s);w.u(1);w.u(1);w.u(1);w.src(s)
 w.u(1);w.t(e['target']);w.r(e['population']);w.u(1);w.u(1);w.u(ordinal);w.u(1);w.t(e['target'])
 for u in e['target'][4]:w.u(u)
 w.u(1);w.name(e['target'][5]);w.u(1);w.r(ref(199));w.u(1);w.u(1);w.r(e['target'][0][2]);w.u(1);w.u(1);w.u(1);w.u(1);w.name(b'client backend')
 return bytes(w.b)+hashlib.sha256(w.b).digest()
e={r:expect(r) for r in (1,2)}
f={r:frame(r,e[r]) for r in e}
print(json.dumps({'case':'baseline','result':m.reconstruct_pair_constraints(e,(f[1],f[2]),400)}))
print(json.dumps({'case':'ordinal_outside_population','result':m.reconstruct_pair_constraints(e,(frame(1,e[1],0xffffffff),f[2]),400)}))
class Frames:
 def __init__(self):self.count=0
 def __iter__(self):
  for _ in range(100):self.count+=1;yield f[1]
g=Frames()
try:m.reconstruct_pair_constraints(e,g,400)
except Exception as x:print(json.dumps({'case':'unbounded_pair_collection','consumed':g.count,'error':str(x)}))
e2={r:expect(r) for r in (1,2)}
for r in e2:
 t=e2[r]['target'];e2[r]['target']=t[:-1]+(b'reader\xc2\x85',);e2[r]['members']=(e2[r]['target'],)
print(json.dumps({'case':'unicode_C1_control','result':m.reconstruct_pair_constraints(e2,(frame(1,e2[1]),frame(2,e2[2])),400)}))
