import socket
import threading
import time
import ssl
import requests
import struct
from dnslib import DNSRecord, QTYPE

class ParallelResolver:
    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = bootstrap_servers if bootstrap_servers else ["1.1.1.1", "8.8.8.8"]
        self.ip_cache = {}
        self.cache_lock = threading.Lock()

    def resolve_bootstrap(self, hostname):
        with self.cache_lock:
            if hostname in self.ip_cache:
                return self.ip_cache[hostname]
                
        try:
            q = DNSRecord.question(hostname)
            for bs in self.bootstrap_servers:
                bs_ip = bs.split(':')[0]
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2.0)
                try:
                    sock.sendto(q.pack(), (bs_ip, 53))
                    resp, _ = sock.recvfrom(2048)
                    d = DNSRecord.parse(resp)
                    ips = [str(r.rdata) for r in d.rr if r.rtype == 1]
                    if ips:
                        with self.cache_lock:
                            self.ip_cache[hostname] = ips[0]
                        return ips[0]
                except:
                    pass
                finally:
                    sock.close()
        except:
            pass
        return hostname # Fallback to letting system resolve if bootstrap fails

    def query_udp(self, server, port, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        try:
            sock.sendto(data, (server, port))
            resp, _ = sock.recvfrom(4096)
            return resp
        except:
            return None
        finally:
            sock.close()

    def query_tcp(self, server, port, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        try:
            sock.connect((server, port))
            sock.sendall(struct.pack('!H', len(data)) + data)
            l_data = sock.recv(2)
            if not l_data: return None
            l = struct.unpack('!H', l_data)[0]
            resp = sock.recv(l)
            return resp
        except:
            return None
        finally:
            sock.close()

    def query_tls(self, server, port, data, hostname=None):
        ip = self.resolve_bootstrap(server)
        context = ssl.create_default_context()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        try:
            wrapped_sock = context.wrap_socket(sock, server_hostname=hostname or server)
            wrapped_sock.connect((ip, port))
            wrapped_sock.sendall(struct.pack('!H', len(data)) + data)
            l_data = wrapped_sock.recv(2)
            if not l_data: return None
            l = struct.unpack('!H', l_data)[0]
            resp = wrapped_sock.recv(l)
            return resp
        except:
            return None
        finally:
            sock.close()

    def query_https(self, url, data):
        hostname = url.split('/')[2].split(':')[0]
        ip = self.resolve_bootstrap(hostname)
        direct_url = url.replace(hostname, ip)
        
        headers = {
            "Content-Type": "application/dns-message",
            "Host": hostname
        }
        try:
            r = requests.post(direct_url, headers=headers, data=data, timeout=2.0, verify=False)
            if r.status_code == 200:
                return r.content
        except:
            pass
        return None

    def query_server(self, server_str, data):
        server_str = server_str.strip()
        if server_str.startswith('https://') or server_str.startswith('h3://'):
            url = server_str.replace('h3://', 'https://')
            return self.query_https(url, data)
        elif server_str.startswith('tls://') or server_str.startswith('quic://'):
            # Fallback QUIC to TLS for now
            host = server_str.split('://')[1]
            port = 853
            if ':' in host:
                host, port = host.split(':')
                port = int(port)
            return self.query_tls(host, port, data, hostname=host)
        elif server_str.startswith('tcp://'):
            host = server_str.split('://')[1]
            port = 53
            if ':' in host:
                host, port = host.split(':')
                port = int(port)
            return self.query_tcp(host, port, data)
        elif server_str.startswith('udp://'):
            host = server_str.split('://')[1]
            port = 53
            if ':' in host:
                host, port = host.split(':')
                port = int(port)
            return self.query_udp(host, port, data)
        elif server_str.startswith('sdns://'):
            # SDNS not fully implemented without external lib, gracefully fail
            return None
        else:
            # Plain IP/Domain
            host = server_str
            port = 53
            if ':' in host and host.count(':') == 1:
                host, port = host.split(':')
                port = int(port)
            return self.query_udp(host, port, data)

    def resolve_parallel(self, servers, data):
        result = [None, None]
        event = threading.Event()

        def worker(srv):
            resp = self.query_server(srv, data)
            if resp and not event.is_set():
                result[0] = resp
                # Shorten server name for display
                short_name = srv.split('://')[-1].split('/')[0]
                result[1] = short_name
                event.set()

        threads = []
        for srv in servers:
            if not srv or srv.startswith('#'): continue
            t = threading.Thread(target=worker, args=(srv,))
            t.daemon = True
            t.start()
            threads.append(t)

        event.wait(2.0)
        return result[0], result[1]
