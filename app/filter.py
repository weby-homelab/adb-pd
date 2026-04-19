import re
import requests
import os
import ipaddress
import threading
from datetime import datetime

class DNSFilter:
    def __init__(self, blocklists=None, user_rules=None, allowed_clients=None, ignored_domains=None):
        self.blocked_domains = set()
        self.allowed_domains = set() 
        self.ignored_domains = set(ignored_domains) if ignored_domains else set()
        self.allowed_networks = []
        self.allowed_ids = set()
        self.list_metadata = {}
        # Map domain to list name for attribution
        self.domain_to_list = {} 

        if allowed_clients:
            for client in allowed_clients:
                try:
                    if '/' in client: self.allowed_networks.append(ipaddress.ip_network(client, strict=False))
                    else:
                        ipaddress.ip_address(client)
                        self.allowed_networks.append(ipaddress.ip_network(client + "/32"))
                except ValueError: self.allowed_ids.add(client.lower())

        if user_rules:
            for rule in user_rules: self.parse_line(rule, "Власні правила")
            
        if blocklists:
            threading.Thread(target=self.load_all_lists, args=(blocklists,), daemon=True).start()

    def update_allowed_clients(self, allowed_clients):
        self.allowed_networks = []
        self.allowed_ids = set()
        if allowed_clients:
            for client in allowed_clients:
                try:
                    if '/' in client: self.allowed_networks.append(ipaddress.ip_network(client, strict=False))
                    else:
                        ipaddress.ip_address(client)
                        self.allowed_networks.append(ipaddress.ip_network(client + "/32"))
                except ValueError: self.allowed_ids.add(client.lower())
        
    def load_all_lists(self, blocklists):
        for bl in blocklists:
            if bl.get('enabled', True):
                count = self.load_from_url(bl['url'], bl.get('name'))
                self.list_metadata[bl['url']] = {
                    "name": bl.get('name'), "count": count,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "enabled": True
                }

    def load_from_url(self, url, list_name):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                lines = response.text.splitlines()
                loaded = 0
                for line in lines:
                    if self.parse_line(line, list_name): loaded += 1
                return loaded
        except Exception: pass
        return 0

    def parse_line(self, line, list_name="Unknown"):
        line = line.strip()
        if not line or line.startswith('!') or line.startswith('['): return False
        is_exception = line.startswith('@@')
        if is_exception: line = line[2:]

        domain = None
        if line.startswith('||'): domain = line[2:].split('^')[0].split('$')[0]
        elif ' ' in line and not line.startswith('/'):
            parts = line.split()
            if len(parts) >= 2 and parts[0] in ['0.0.0.0', '127.0.0.1']: domain = parts[1]
        elif not any(c in line for c in '/$*|'): domain = line

        if domain:
            if is_exception: self.allowed_domains.add(domain)
            else:
                self.blocked_domains.add(domain)
                self.domain_to_list[domain] = list_name
            return True
        return False

    def is_client_allowed(self, client_id):
        if not self.allowed_networks and not self.allowed_ids: return True
        
        # 1. Check ID (Case-insensitive)
        cid = str(client_id).lower().strip()
        if cid in self.allowed_ids: return True
        
        # 2. Check IP/Network
        try:
            ip = ipaddress.ip_address(cid)
            return any(ip in net for net in self.allowed_networks)
        except ValueError:
            # If cid was not an IP, it might be a Client ID that's not in the list
            return False

    def is_ignored(self, domain):
        return domain in self.ignored_domains

    def is_blocked(self, domain):
        domain = domain.rstrip('.')
        # 1. Check Whitelist
        if self._match_set(domain, self.allowed_domains): return False, None
        
        # 2. Check Blacklist
        matched, rule_name = self._match_attr(domain, self.blocked_domains)
        if matched: return True, rule_name
        return False, None

    def _match_set(self, domain, rule_set):
        if domain in rule_set: return True
        parts = domain.split('.')
        for i in range(len(parts) - 1):
            if '.'.join(parts[i+1:]) in rule_set: return True
        return False

    def _match_attr(self, domain, rule_set):
        if domain in rule_set: return True, self.domain_to_list.get(domain, "Фільтр")
        parts = domain.split('.')
        for i in range(len(parts) - 1):
            sub = '.'.join(parts[i+1:])
            if sub in rule_set: return True, self.domain_to_list.get(sub, "Фільтр")
        return False, None

    def discard_rule(self, line):
        line = line.strip()
        is_exception = line.startswith('@@')
        if is_exception: line = line[2:]
        domain = line[2:].split('^')[0].split('$')[0] if line.startswith('||') else line
        if is_exception: self.allowed_domains.discard(domain)
        else:
            self.blocked_domains.discard(domain)
            self.domain_to_list.pop(domain, None)
