LAB 10 - REMOTE DNS CACHE POISONING - STUDENT RESOURCES

CHI SU DUNG TRONG MOI TRUONG AO CO LAP CUA LAB.
Khong chay cac script tren Wi-Fi, mang truong, mang doanh nghiep, Internet hay he thong cua nguoi khac.

LAB 10 ke thua LAB 9:
- pfSense DNSLAB: 10.9.0.1/24
- DNS-SERVER: 10.9.0.10
- VICTIM: 10.9.0.100
- AUTH-DNS/APP-TEST: 172.16.6.20
- DMZ-WEB: 172.16.6.10

LAB 10 bo sung ATTACKNET 10.10.0.0/24, pfSense 10.10.0.1 va chuyen Kali sang 10.10.0.200. Kali khong duoc gan vao DNSLAB trong pha tan cong.

De tai lap co che Kaminsky tren he thong hien dai, pha tan cong su dung lab-vulnerable resolver va AUTH-DNS race relay hard-code theo IP/domain cua LAB 10. BIND9 hien dai duoc dung cho baseline va pha hardening.
