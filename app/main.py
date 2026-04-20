import socket
import sys
import yaml
import threading
import os
import time
import ssl
import base64
import secrets
from datetime import datetime
from collections import deque, Counter
from dnslib import DNSRecord, QTYPE, RR, A
from filter import DNSFilter
from upstream import ParallelResolver
from fastapi import FastAPI, Request, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

proxy_instance = None
query_logs = deque(maxlen=150)
logs_lock = threading.Lock()
stats_lock = threading.Lock()
active_sessions = {}
stats_history = deque(maxlen=60)

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.scheme == "http" and proxy_instance and proxy_instance.config.get('tls', {}).get('force_https'):
            path = request.url.path
            if not path.startswith("/api/") and not path.startswith("/dns-query"):
                return RedirectResponse(url=str(request.url.replace(scheme="https", port=443)))
        return await call_next(request)

app.add_middleware(HTTPSRedirectMiddleware)

def get_current_user(request: Request):
    token = request.cookies.get("dna_session")
    if not token or token not in active_sessions or active_sessions[token] < time.time():
        if proxy_instance and proxy_instance.config.get('auth', {}).get('password'):
            raise HTTPException(status_code=401)
    return True

class UpstreamManager:
    def __init__(self, cfg):
        self.update_config(cfg)
    def update_config(self, cfg):
        self.default = []; self.conditional = {}; self.fallback = cfg.get('dns', {}).get('fallback_dns', [])
        self.bootstrap = cfg.get('dns', {}).get('bootstrap_dns', ['1.1.1.1', '8.8.8.8'])
        for u in cfg.get('dns', {}).get('upstream_dns', []):
            if u.startswith('[/') and '/]' in u:
                parts = u[2:].split('/]'); doms = parts[0].split(',')
                for d in doms: self.conditional[d.strip('.').lower()] = parts[1].split()
            else: self.default.append(u)
        self.resolver = ParallelResolver(self.bootstrap)
    def resolve(self, qname, data):
        qname = qname.lower().strip('.')
        for dom, srvs in self.conditional.items():
            if qname == dom or qname.endswith('.' + dom):
                res, used = self.resolver.resolve_parallel(srvs, data)
                if res: return res, f"Up: {used}"
        res, used = self.resolver.resolve_parallel(self.default, data)
        if res: return res, f"Паралельний ({used})"
        if self.fallback:
            res, used = self.resolver.resolve_parallel(self.fallback, data)
            if res: return res, f"Резервний ({used})"
        return None, None

class RateLimiter:
    def __init__(self, limit):
        self.limit = limit; self.clients = {}; self.lock = threading.Lock(); self.last = time.time()
    def is_allowed(self, ip):
        if self.limit <= 0: return True
        now = time.time()
        with self.lock:
            if now - self.last > 60: self.clients = {k: v for k, v in self.clients.items() if any(now-t < 1 for t in v)}; self.last = now
            h = [t for t in self.clients.get(ip, []) if now-t < 1]
            if len(h) >= self.limit: return False
            h.append(now); self.clients[ip] = h; return True

class DNSProxy:
    def __init__(self, config_path=None):
        global proxy_instance
        proxy_instance = self
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(self.config_path, 'r') as f: self.config = yaml.safe_load(f)
        cfg = self.config
        self.filter = DNSFilter(
            blocklists=cfg.get('filtering', {}).get('blocklists', []),
            user_rules=cfg.get('filtering', {}).get('user_rules', []),
            allowed_clients=cfg.get('dns', {}).get('allowed_clients', []),
            ignored_domains=cfg.get('dns', {}).get('blocked_hosts', [])
        )
        self.up_mgr = UpstreamManager(cfg)
        self.rewrites = cfg.get('dns', {}).get('rewrites', {})
        self.rate_limiter = RateLimiter(cfg.get('dns', {}).get('ratelimit', 60))
        self.stats = {"total": 0, "blocked": 0, "start": time.time(), "time": 0, "clients": Counter(), "domains": Counter()}
        threading.Thread(target=self.stats_collector, daemon=True).start()

    def stats_collector(self):
        while True:
            with stats_lock: stats_history.append({"timestamp": datetime.now().strftime("%H:%M"), "total": self.stats["total"], "blocked": self.stats["blocked"]})
            time.sleep(60)

    def log_query(self, cid, ip, qname, proto, qtype, status, ms, rule, ans):
        display = f"{cid} ({ip})" if cid != ip else str(ip)
        entry = {"time": datetime.now().strftime("%H:%M:%S"), "date": datetime.now().strftime("%d.%m.%Y"), "client": display, "domain": qname, "type": f"{qtype}, {proto}", "status": status, "time_ms": ms, "rule": rule, "answer": ans}
        with logs_lock: query_logs.appendleft(entry)

    def process(self, data, cid, ip, proto="UDP"):
        start = time.perf_counter()
        if not self.filter.is_client_allowed(cid) and not self.filter.is_client_allowed(ip):
            self.log_query(cid, ip, "Unknown", proto, "ANY", "DENIED", 0, "ACL Блокування", "-"); return None
        if not self.rate_limiter.is_allowed(ip): return None
        try:
            req = DNSRecord.parse(data); qname = str(req.q.qname).rstrip('.'); qtype = str(QTYPE.get(req.q.qtype, req.q.qtype))
            if self.filter.is_ignored(qname): return None
            if qtype == 'A' and qname in self.rewrites:
                ans = self.rewrites[qname]; self.log_query(cid, ip, qname, proto, qtype, "REWRITE", 0, "Власний хост", ans)
                with stats_lock: self.stats["total"] += 1; self.stats["clients"][client_display_name(cid, ip)]+=1; return req.reply().add_answer(RR(qname, QTYPE.A, rdata=A(ans), ttl=300)).pack()
            blocked, rule = self.filter.is_blocked(qname)
            if blocked:
                self.log_query(cid, ip, qname, proto, qtype, "BLOCKED", 0, rule, "0.0.0.0")
                with stats_lock: self.stats["blocked"] += 1
                rep = req.reply(); rep.header.rcode = 3; return rep.pack()
            resp, used_rule = self.up_mgr.resolve(qname, data)
            if resp:
                ms = round((time.perf_counter()-start)*1000, 2)
                self.log_query(cid, ip, qname, proto, qtype, "ALLOWED", ms, used_rule, self.get_ans_info(resp))
                with stats_lock: self.stats["total"] += 1; self.stats["clients"][client_display_name(cid, ip)]+=1; self.stats["time"] += (ms/1000)
                return resp
        except: pass
        return None

    def get_ans_info(self, data):
        try:
            d = DNSRecord.parse(data); ips = [str(r.rdata) for r in d.rr if r.rtype == 1]
            return ", ".join(ips) if ips else "-"
        except: return "-"

    def udp_loop(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind((self.config['dns'].get('bind_host', '0.0.0.0'), self.config['dns'].get('port', 53)))
        print("DNS UDP online")
        while True:
            try: d, a = s.recvfrom(1024); threading.Thread(target=lambda: s.sendto(self.process(d, a[0], a[0], "UDP"), a) if self.process(d, a[0], a[0], "UDP") else None, daemon=True).start()
            except: pass

    def dot_loop(self):
        t = self.config.get('tls', {})
        if not t.get('enabled'): return
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(t['certificate_path'], t['private_key_path'])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.bind((self.config['dns'].get('bind_host', '0.0.0.0'), t.get('port_dot', 853))); s.listen(100)
        print("DNS DoT online")
        while True:
            try:
                c, a = s.accept()
                threading.Thread(target=self.handle_dot, args=(c, a, ctx), daemon=True).start()
            except: pass

    def handle_dot(self, c, a, ctx):
        try:
            ss = ctx.wrap_socket(c, server_side=True)
            sni = (ss.server_hostname or "").lower().rstrip('.')
            base = self.config.get('tls', {}).get('server_name', '').lower().rstrip('.')
            ip = a[0]; cid = ip
            if sni and base and sni.endswith(base): cid = "General" if sni == base else sni.replace('.' + base, '')
            while True:
                l_data = ss.recv(2)
                if not l_data: break
                l = int.from_bytes(l_data, 'big'); d = ss.recv(l); r = self.process(d, cid, ip, "TLS")
                if r: ss.sendall(len(r).to_bytes(2, 'big') + r)
        except: pass
        finally: c.close()

    def start(self):
        threading.Thread(target=self.udp_loop, daemon=True).start()
        threading.Thread(target=self.dot_loop, daemon=True).start()
        ui = os.path.join(os.path.dirname(__file__), 'ui')
        app.mount("/static", StaticFiles(directory=ui), name="static")
        @app.get("/", response_class=HTMLResponse)
        def index(): return open(os.path.join(ui, "index.html")).read()
        t = self.config.get('tls', {})
        if t.get('enabled'):
            threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=80), daemon=True).start()
            hc = Config(); hc.bind = ["0.0.0.0:443"]; hc.certfile = t['certificate_path']; hc.keyfile = t['private_key_path']; hc.alpn_protocols = ["h2", "http/1.1"]
            asyncio.run(serve(app, hc))
        else: uvicorn.run(app, host="0.0.0.0", port=8080)

def client_display_name(cid, ip): return f"{cid} ({ip})" if cid != ip else str(ip)

@app.get("/api/auth/status")
def auth_status(): return {"status": "setup" if not proxy_instance.config.get('auth', {}).get('password') else "ready"}
@app.post("/api/auth/login")
async def auth_login(request: Request, response: Response):
    d = await request.json(); pwd = d.get("password")
    if pwd == proxy_instance.config.get('auth', {}).get('password'):
        token = secrets.token_hex(32); active_sessions[token] = time.time() + 86400
        response.set_cookie(key="dna_session", value=token, httponly=True, samesite="lax", path="/"); return {"status": "success"}
    raise HTTPException(status_code=401)
@app.get("/api/stats", dependencies=[Depends(get_current_user)])
def get_stats():
    with stats_lock:
        s = proxy_instance.stats; avg = (s["time"]/s["total"]*1000) if s["total"]>0 else 0
        return {"total_queries": s["total"], "blocked_queries": s["blocked"], "avg_processing_time_ms": round(avg, 1), "top_clients": dict(s["clients"].most_common(10)), "top_domains": dict(s["domains"].most_common(15)), "history": list(stats_history), "active_rules": len(proxy_instance.filter.blocked_domains), "uptime": int(time.time() - s["start"])}
@app.get("/api/logs", dependencies=[Depends(get_current_user)])
def get_logs(search: str = None):
    with logs_lock: logs = list(query_logs)
    return [l for l in logs if not search or search.lower() in l["domain"].lower() or search.lower() in l["client"].lower()]
@app.get("/api/dns/settings", dependencies=[Depends(get_current_user)])
def get_dns_settings(): return {"upstream_dns": "\n".join(proxy_instance.config['dns'].get('upstream_dns', [])), "fallback_dns": "\n".join(proxy_instance.config['dns'].get('fallback_dns', [])), "bootstrap_dns": "\n".join(proxy_instance.config['dns'].get('bootstrap_dns', []))}
@app.post("/api/dns/settings/update", dependencies=[Depends(get_current_user)])
async def update_dns_settings(request: Request):
    d = await request.json(); proxy_instance.config['dns']['upstream_dns'] = [u.strip() for u in d.get('upstream_dns', '').split('\n') if u.strip()]; proxy_instance.config['dns']['fallback_dns'] = [u.strip() for u in d.get('fallback_dns', '').split('\n') if u.strip()]; proxy_instance.config['dns']['bootstrap_dns'] = [u.strip() for u in d.get('bootstrap_dns', '').split('\n') if u.strip()]; proxy_instance.save_config(); proxy_instance.up_mgr.update_config(proxy_instance.config); return {"status": "success"}
@app.get("/api/access/allowed", dependencies=[Depends(get_current_user)])
def get_acc(): return proxy_instance.config['dns'].get('allowed_clients', [])
@app.post("/api/access/allowed/update", dependencies=[Depends(get_current_user)])
async def up_acc(request: Request): d = await request.json(); c = d.get("clients"); proxy_instance.config['dns']['allowed_clients'] = c; proxy_instance.save_config(); proxy_instance.filter.update_allowed_clients(c); return {"status":"success"}
@app.get("/api/blocklists", dependencies=[Depends(get_current_user)])
def get_bl(): return [{"name": b['name'], "url": b['url'], "rule_count": proxy_instance.filter.list_metadata.get(b['url'], {}).get('count', 0)} for b in proxy_instance.config['filtering'].get('blocklists', [])]
@app.post("/api/blocklists/add", dependencies=[Depends(get_current_user)])
async def add_bl(request: Request): d = await request.json(); name = d.get("name"); url = d.get("url", "").strip(); lists = proxy_instance.config['filtering'].setdefault('blocklists', []); lists.append({"name": name, "url": url, "enabled": True}); proxy_instance.save_config(); threading.Thread(target=proxy_instance.filter.load_all_lists, args=([lists[-1]],), daemon=True).start(); return {"status": "success"}
@app.post("/api/blocklists/remove", dependencies=[Depends(get_current_user)])
async def rm_bl(request: Request): d = await request.json(); url = d.get("url", "").strip(); proxy_instance.config['filtering']['blocklists'] = [l for l in proxy_instance.config['filtering'].get('blocklists', []) if l['url'].strip() != url]; proxy_instance.save_config(); return {"status":"success"}
@app.get("/api/rules", dependencies=[Depends(get_current_user)])
def get_rules(): return proxy_instance.config['filtering'].get('user_rules', [])
@app.post("/api/rules/add", dependencies=[Depends(get_current_user)])
async def add_rule(request: Request): d = await request.json(); r = d.get("rule"); rules = proxy_instance.config['filtering'].setdefault('user_rules', []); rules.append(r); proxy_instance.filter.parse_line(r, "Власні правила"); proxy_instance.save_config(); return {"status":"success"}
@app.post("/api/rules/remove", dependencies=[Depends(get_current_user)])
async def rm_rule(request: Request): d = await request.json(); r = d.get("rule"); proxy_instance.config['filtering']['user_rules'].remove(r); proxy_instance.filter.discard_rule(r); proxy_instance.save_config(); return {"status":"success"}
@app.get("/api/rewrites", dependencies=[Depends(get_current_user)])
def get_rw(): return [{"domain": k, "ip": v} for k, v in proxy_instance.rewrites.items()]
@app.post("/api/rewrites/add", dependencies=[Depends(get_current_user)])
async def add_rw(request: Request): d = await request.json(); dom = d.get("domain"); ip = d.get("ip"); proxy_instance.rewrites[dom] = ip; proxy_instance.config.setdefault('dns', {})['rewrites'] = proxy_instance.rewrites; proxy_instance.save_config(); return {"status": "success"}
@app.post("/api/rewrites/remove", dependencies=[Depends(get_current_user)])
async def rm_rw(request: Request): d = await request.json(); dom = d.get("domain"); del proxy_instance.rewrites[dom]; proxy_instance.config['dns']['rewrites'] = proxy_instance.rewrites; proxy_instance.save_config(); return {"status": "success"}
@app.api_route("/dns-query", methods=["GET", "POST"])
@app.api_route("/dns-query/{client_id}", methods=["GET", "POST"])
async def doh(request: Request, client_id: str = "DOH"):
    msg = await request.body() if request.method == "POST" else None
    if not msg:
        b64 = request.query_params.get("dns")
        if b64: msg = base64.urlsafe_b64decode(b64 + "="*((4-len(b64)%4)%4))
    if not msg: return Response(status_code=400)
    ip = request.headers.get("x-forwarded-for") or request.headers.get("cf-connecting-ip") or request.client.host
    if ',' in ip: ip = ip.split(',')[0].strip()
    res = proxy_instance.process(msg, client_id, ip, "DoH")
    return Response(content=res, media_type="application/dns-message") if res else Response(status_code=204)

if __name__ == "__main__": DNSProxy().start()
