import pathlib,threading,http.server,json,socket,subprocess,os,time
O=pathlib.Path(__file__).resolve().parent;R=pathlib.Path.cwd();requests=[]
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_OPTIONS(self):
  self.send_response(204);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','Content-Type,Authorization');self.send_header('Access-Control-Allow-Methods','GET');self.end_headers()
 def do_GET(self):
  requests.append({'method':'GET','path':self.path});body=json.dumps({'code':'SYNTHETIC_DEPENDENCY_UNAVAILABLE','detail':'Controlled isolated failure injection only'}).encode();self.send_response(503);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
env=os.environ.copy();env['VITE_API_BASE_URL']='http://127.0.0.1:'+str(server.server_port);env['VITE_DEMO_MODE']='false'
cmd=['node.exe',str(R/'applications/economic-decision-room-web/node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port',str(port),'--strictPort']
log=(O/'negative-browser-vite.log').open('w');child=subprocess.Popen(cmd,cwd=R/'applications/economic-decision-room-web',env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
(O/'negative-browser-runtime.json').write_text(json.dumps({'frontend_url':'http://127.0.0.1:'+str(port),'controlled_failure_url':env['VITE_API_BASE_URL'],'child_pid':child.pid,'scope':'Real frontend plus explicit503failure injector, NOT real integrated backend/DB or positive golden path','token_or_credentials':'NONE','timeout_seconds':300},indent=2))
print(json.dumps({'frontend_url':'http://127.0.0.1:'+str(port),'failure_port':server.server_port}),flush=True)
try:
 for i in range(300):
  if child.poll() is not None:raise RuntimeError('Owned Vite exited')
  if (O/'stop-negative-browser').exists():break
  time.sleep(1)
finally:
 child.terminate();child.wait(timeout=15);server.shutdown();server.server_close();log.close();(O/'negative-browser-requests.json').write_text(json.dumps({'requests':requests,'cleanup':'Owned Vite and injector stopped'},indent=2))
