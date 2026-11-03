Kali phai chi con card ATTACKNET 10.10.0.200/24 trong pha tan cong; Promiscuous Mode = Deny.
Cai: sudo apt install -y python3-dnspython dnsutils
Terminal 1: sudo python3 evil_dns_lab10.py
Terminal 2: sudo python3 -m http.server 80 --directory <thu_muc_fake_site>
Terminal 3: python3 kaminsky_remote_lab10.py
Script kaminsky gui query va cac khoang TXID toi race relay; khong sniff DNSLAB va khong tao flood 65,536 packet.
