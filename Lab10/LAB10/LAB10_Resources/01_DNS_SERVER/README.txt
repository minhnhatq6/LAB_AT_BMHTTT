Baseline: dung BIND9 voi named.conf.options.baseline + named.conf.local.baseline.
Attack phase: stop bind9 roi chay sudo python3 vuln_resolver_lab10.py. Script chi bind 10.9.0.10:53 va source port 33333, chi nhan query tu 10.9.0.100/10.10.0.200.
Hardening: dung script, khoi dong lai BIND9 va kiem tra source port random bang tcpdump/Wireshark.
Cai dependency: sudo apt install -y python3-dnspython dnsutils
