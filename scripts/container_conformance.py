"""Black-box checks for the documented Docker worker boundary."""
from __future__ import annotations

import argparse
import json
import subprocess

BASE=["docker","run","--rm","--network=none","--read-only","--cap-drop=ALL","--security-opt=no-new-privileges","--pids-limit=64","--memory=128m","--user=65532:65532","--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m"]

def run(image, command, payload="{}"):
    return subprocess.run([*BASE,image,*command],input=payload,text=True,capture_output=True,timeout=20,check=False)

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("image",help="digest-pinned reference image"); a=p.parse_args()
    if "@sha256:" not in a.image: raise SystemExit("image must be pinned by sha256 digest")
    probe="""import json,os,socket
r={"uid":os.getuid(),"root_write":True,"network":True,"tmp_write":False}
try: open('/blocked','w').write('x')
except OSError: r['root_write']=False
try: socket.create_connection(('1.1.1.1',53),1)
except OSError: r['network']=False
try: open('/tmp/ok','w').write('x'); r['tmp_write']=True
except OSError: pass
print(json.dumps(r))"""
    result=run(a.image,["python","-c",probe]);
    if result.returncode: raise SystemExit(result.stderr)
    observed=json.loads(result.stdout)
    expected={"uid":65532,"root_write":False,"network":False,"tmp_write":True}
    if observed!=expected: raise SystemExit(f"conformance failed: {observed!r}")
    echo=run(a.image,[],json.dumps({"probe":"echo"}))
    if echo.returncode or json.loads(echo.stdout)!={"probe":"echo"}: raise SystemExit("reference worker JSON protocol failed")
    print("PASS: non-root, read-only root, writable bounded tmpfs, network denied, JSON protocol")
if __name__=="__main__": main()
