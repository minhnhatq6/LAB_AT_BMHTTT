#!/usr/bin/env python3
import socket, ipaddress
import dns.message, dns.rrset, dns.rdatatype, dns.rcode, dns.flags
IP='10.10.0.200'; ZONE='example.lab10.test.'; NS='ns.evil.example.lab10.test.'
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.bind((IP,53)); print(f'LAB10 evil authoritative DNS {IP}:53 for {ZONE}')
while True:
    data,addr=s.recvfrom(4096)
    try: q=dns.message.from_wire(data)
    except Exception: continue
    if len(q.question)!=1: continue
    name=str(q.question[0].name).lower(); r=dns.message.make_response(q); r.flags|=dns.flags.AA
    if not name.endswith(ZONE): r.set_rcode(dns.rcode.REFUSED)
    elif q.question[0].rdtype==dns.rdatatype.NS:
        r.answer.append(dns.rrset.from_text(ZONE,300,'IN','NS',NS)); r.additional.append(dns.rrset.from_text(NS,300,'IN','A',IP))
    else: r.answer.append(dns.rrset.from_text(name,60,'IN','A',IP))
    s.sendto(r.to_wire(),addr); print('answered',name,'to',addr)
