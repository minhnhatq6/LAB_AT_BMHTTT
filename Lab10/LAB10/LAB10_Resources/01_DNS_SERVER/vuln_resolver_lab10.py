#!/usr/bin/env python3
import socket, threading, random, time, ipaddress
import dns.message, dns.rdatatype, dns.rcode, dns.rrset

BIND_IP='10.9.0.10'; LISTEN_PORT=53; UPSTREAM_PORT=33333
LEGIT_NS='172.16.6.20'; EVIL_IP='10.10.0.200'; ZONE='example.lab10.test.'
ALLOWED_CLIENTS={'10.9.0.100','10.10.0.200'}

class Resolver:
    def __init__(self):
        self.ns_ip=LEGIT_NS; self.ns_name='ns.legit.example.lab10.test.'; self.poisoned=False
        self.in_sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); self.in_sock.bind((BIND_IP,LISTEN_PORT))
        self.up_sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); self.up_sock.bind((BIND_IP,UPSTREAM_PORT)); self.up_sock.settimeout(5)
        self.lock=threading.Lock()
    def cache_referral(self,resp):
        ns=None; glue=None
        for rrset in resp.authority:
            if rrset.rdtype==dns.rdatatype.NS and str(rrset.name).lower()==ZONE:
                ns=str(next(iter(rrset)).target)
        if ns:
            for rrset in resp.additional:
                if rrset.rdtype==dns.rdatatype.A and str(rrset.name).lower()==ns.lower():
                    glue=str(next(iter(rrset)))
        if ns and glue:
            ipaddress.ip_address(glue)
            if glue!=EVIL_IP: return
            self.ns_name=ns; self.ns_ip=glue; self.poisoned=True
            print(f'[CACHE] delegation poisoned: {ZONE} NS {ns} -> {glue}')
    def handle(self,data,addr):
        if addr[0] not in ALLOWED_CLIENTS: return
        try: q=dns.message.from_wire(data)
        except Exception: return
        if len(q.question)!=1: return
        qname=str(q.question[0].name).lower()
        if not qname.endswith(ZONE):
            r=dns.message.make_response(q); r.set_rcode(dns.rcode.REFUSED); self.in_sock.sendto(r.to_wire(),addr); return
        up=dns.message.make_query(q.question[0].name,q.question[0].rdtype)
        up.id=random.randrange(0,65536)
        target=self.ns_ip
        print(f'[QUERY] client={addr[0]} q={qname} upstream={target}:53 txid={up.id} srcport={UPSTREAM_PORT}')
        with self.lock:
            self.up_sock.sendto(up.to_wire(),(target,53))
            try: wire,src=self.up_sock.recvfrom(4096)
            except socket.timeout:
                r=dns.message.make_response(q); r.set_rcode(dns.rcode.SERVFAIL); self.in_sock.sendto(r.to_wire(),addr); return
        try: resp=dns.message.from_wire(wire)
        except Exception:
            r=dns.message.make_response(q); r.set_rcode(dns.rcode.SERVFAIL); self.in_sock.sendto(r.to_wire(),addr); return
        if resp.id!=up.id:
            print(f'[DROP] txid mismatch got={resp.id} expected={up.id}')
            r=dns.message.make_response(q); r.set_rcode(dns.rcode.SERVFAIL); self.in_sock.sendto(r.to_wire(),addr); return
        if src[0] not in {LEGIT_NS,EVIL_IP} or src[1]!=53:
            print('[DROP] unexpected source',src); return
        self.cache_referral(resp)
        resp.id=q.id
        self.in_sock.sendto(resp.to_wire(),addr)
    def run(self):
        print(f'LAB10 vulnerable resolver on {BIND_IP}:53; upstream source port {UPSTREAM_PORT}')
        print('Hard-coded lab scope only. Ctrl+C to stop.')
        while True:
            data,addr=self.in_sock.recvfrom(4096); threading.Thread(target=self.handle,args=(data,addr),daemon=True).start()

if __name__=='__main__': Resolver().run()
