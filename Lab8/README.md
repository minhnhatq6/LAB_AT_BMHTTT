# BÁO CÁO THỰC HÀNH LAB 8: LOCAL DNS ATTACK - DNS SPOOFING VÀ CACHE POISONING TRÊN MÔ HÌNH pfSense + BIND9

## 1. Thông tin sinh viên
- **Họ và tên:** ĐẶNG MINH NHẬT
- **MSSV:** 1150080029
- **Mã lớp:** 11DHCNPM1
- **Môn học:** An toàn hệ thống thông tin
- **Nền tảng ảo hóa:** VMware Workstation / VirtualBox
- **Link Video minh chứng thực hành:** https://youtu.be/nOJYesAsH_k

---

## 2. Kiến trúc giải pháp và Phân hoạch mạng DNS-LAB

Mô hình bài thực hành kế thừa hạ tầng phân tầng an ninh từ các bài Lab trước (WAN, LAN-DOMAIN, DMZ, MGMT) và mở rộng thêm một giao diện mạng nội bộ chuyên dụng **OPT2 (DNSLAB - `10.9.0.0/24`)** trên Tường lửa Gateway pfSense nhằm phục vụ các kịch bản kiểm thử tấn công DNS độc lập, an toàn:

### 2.1. Phân tầng kiến trúc hạ tầng
- **pfSense CE (Firewall/Gateway L3/L4):**
  - **WAN:** Nhận IP tự động qua DHCP/NAT từ hạ tầng vật lý bên ngoài.
  - **MGMT (`192.168.56.254/24`):** Giao diện quản trị WebGUI riêng biệt, cô lập khỏi mạng người dùng.
  - **LAN-DOMAIN (`10.6.0.0/24`):** Chứa Domain Controller (DC01) Active Directory và các dịch vụ miền cốt lõi, được bảo vệ tuyệt đối bằng luật Block từ DNSLAB.
  - **DMZ (`172.16.6.0/24`):** Chứa máy chủ Web dịch vụ **DMZ-WEB** (`172.16.6.10`) và máy chủ Authoritative DNS mô phỏng **APP-TEST** (`172.16.6.20`).
  - **DNSLAB (`10.9.0.1/24` - OPT2):** Phân vùng mạng nội bộ thử nghiệm (không gán Upstream Gateway).
  - **Ma trận chính sách Firewall DNSLAB (Firewall Ruleset):**
    1. *Rule 1 (PASS):* Cho phép `10.9.0.10` (DNS-SERVER) kết nối tới `172.16.6.20` cổng `UDP/TCP 53` (Authoritative DNS).
    2. *Rule 2 (PASS):* Cho phép dải `10.9.0.0/24` kết nối tới `172.16.6.10` cổng `TCP 80` (DMZ Web Server).
    3. *Rule 3 (BLOCK + LOG):* Chặn toàn bộ lưu lượng từ `10.9.0.0/24` sang `10.6.0.0/24` (bảo vệ LAN-DOMAIN DC01).
    4. *Rule 4 (BLOCK + LOG):* Chặn toàn bộ lưu lượng từ `10.9.0.0/24` sang `192.168.56.0/24` (bảo vệ MGMT pfSense).
    5. *Rule 5 (BLOCK + LOG):* Chặn toàn bộ lưu lượng từ `10.9.0.0/24` đi ra các mạng khác/WAN trong pha tấn công.

- **DNS-SERVER (Recursive & Caching Resolver - Ubuntu Server 24.04 LTS):**
  - Địa chỉ IP tĩnh: `10.9.0.10/24`, Gateway `10.9.0.1`.
  - Cấu hình dịch vụ BIND9:
    - Đóng vai trò Recursive Resolver cho các máy trạm trong dải `10.9.0.0/24`.
    - Authoritative cho zone cục bộ `lab9.test` và `9.10.in-addr.arpa`.
    - Cấu hình Forward zone `external.lab9.test` chuyển tiếp truy vấn đệ quy sang `172.16.6.20`.
    - Cấu hình đặc biệt phục vụ nghiên cứu: `server 172.16.6.20 { send-cookie no; };` nhằm vô hiệu hóa cơ chế DNS Cookie đối với server mô phỏng, cho phép tái lập tấn công On-path Spoofing.

- **VICTIM (Client máy nạn nhân - Ubuntu Desktop 24.04 LTS):**
  - Địa chỉ IP tĩnh: `10.9.0.100/24`, Gateway `10.9.0.1`.
  - Cấu hình Netplan trỏ DNS duy nhất về máy chủ nội bộ `10.9.0.10`.

- **ATTACKER (Máy kẻ tấn công - Kali Linux):**
  - Địa chỉ IP: `10.9.0.200/24`.
  - Card mạng gắn phân đoạn `dns-lab` thiết lập chế độ **Promiscuous Mode = Allow VMs**, cho phép bắt toàn bộ khung tin Unicast truyền giữa Victim và DNS-SERVER.
  - Sử dụng thư viện Scapy (`dns_spoof_lab9.py`) để sniff gói tin DNS UDP/53 và bơm gói phản hồi giả mạo theo 2 chế độ (`mode victim` và `mode resolver`).
  - Chạy máy chủ Web Python (cổng 80) phục vụ trang web giả lập cảnh báo điều hướng (`fake_index.html`).

- **Hạ tầng dịch vụ DMZ hỗ trợ kiểm thử:**
  - **DMZ-WEB (`172.16.6.10`):** Máy chủ Nginx chính thống cung cấp website đích.
  - **APP-TEST / AUTH-DNS (`172.16.6.20`):** Daemon Python (`auth_dns_delayed.py`) đóng vai trò Authoritative DNS quản lý `www.external.lab9.test -> 172.16.6.10` với độ trễ cố ý `1.5 giây` để mô phỏng độ trễ đường truyền Internet và tạo điều kiện quan sát cuộc đua gói tin.

### 2.2. Bảng phân hoạch địa chỉ IP chi tiết
| Thành phần / Máy ảo | Hệ điều hành / Vai trò | Địa chỉ IP / Mask | Ghi chú vai trò |
| :--- | :--- | :--- | :--- |
| **pfSense Gateway** | FreeBSD 14 / Firewall L3-L4 | `10.9.0.1/24` (DNSLAB)<br>`172.16.6.1/24` (DMZ)<br>`192.168.56.254` (MGMT) | Cổng phân đoạn mạng, thực thi Firewall Rules |
| **DNS-SERVER** | Ubuntu Server 24.04 LTS<br>BIND9 Resolver | `10.9.0.10/24` (GW: `10.9.0.1`) | Máy chủ phân giải tên miền nội bộ DNSLAB |
| **VICTIM** | Ubuntu Desktop 24.04 LTS<br>Máy trạm Client | `10.9.0.100/24` (DNS: `10.9.0.10`) | Nạn nhân trong các kịch bản chuyển hướng |
| **ATTACKER (Kali)** | Kali Linux 2024.x<br>Scapy & Wireshark | `10.9.0.200/24` (Promisc: Allow VMs) | Kẻ tấn công cùng mạng cục bộ (On-path) |
| **DMZ-WEB** | Ubuntu Server 24.04 / Nginx | `172.16.6.10/24` | Máy chủ web hợp lệ cung cấp dịch vụ gốc |
| **APP-TEST / AUTH**| Python Daemon / Socket UDP 53 | `172.16.6.20/24` (Delay: 1.5s) | Authoritative DNS mô phỏng quản lý external zone |
| **HOST MGMT** | Windows Host / Trình duyệt | `192.168.56.1/24` | Quản trị WebGUI pfSense tách biệt an toàn |

---

## 3. Nội dung và Kết quả thực nghiệm chi tiết

### 3.1. Giai đoạn 1: Chuẩn bị môi trường & Xác lập Baseline sạch
1. **Kiểm tra cú pháp cấu hình BIND9 trên DNS-SERVER:**
   - Thực thi `sudo named-checkconf` $\rightarrow$ Không có lỗi cú pháp.
   - Thực thi `sudo named-checkzone lab9.test /etc/bind/db.lab9.test` $\rightarrow$ Trả về `OK` (serial 2026101101).
   - Thực thi `sudo named-checkzone 9.10.in-addr.arpa /etc/bind/db.10.9.0` $\rightarrow$ Trả về `OK`.
   - Khởi động lại dịch vụ: `sudo systemctl restart bind9` (trạng thái `active (running)`).
2. **Khởi chạy Authoritative DNS và Web Server giả lập:**
   - Trên APP-TEST (`172.16.6.20`): `sudo python3 auth_dns_delayed.py --bind 172.16.6.20 --delay 1.5`
   - Trên Kali (`10.9.0.200`): `sudo python3 -m http.server 80` trong thư mục chứa `fake_index.html`.
3. **Kiểm tra Baseline từ máy Victim:**
   - Chạy `dig @10.9.0.10 www.external.lab9.test` $\rightarrow$ Nhận câu trả lời `172.16.6.10` sau thời gian `1512 msec` (khớp với delay 1.5s từ AUTH-DNS).
   - Chạy `curl -I http://www.external.lab9.test` $\rightarrow$ Trả về `HTTP/1.1 200 OK` từ máy chủ Nginx DMZ-WEB.
   - *Kết luận:* Trạng thái Baseline hoàn toàn sạch sẽ và phân giải chính xác trước khi tấn công.

---

### 3.2. Giai đoạn 2: Task 1 - Chuyển hướng tên miền bằng tệp `/etc/hosts`
- **Nguyên lý:** Thư viện C chuẩn (`glibc`) tuân thủ quy tắc trong `/etc/nsswitch.conf` (`hosts: files dns`), kiểm tra tệp tĩnh `/etc/hosts` trước khi gửi truy vấn DNS ra mạng.
- **Thực thi:** Trên máy Victim, thêm dòng ánh xạ:
  ```bash
  echo "10.9.0.200 www.lab9.test" | sudo tee -a /etc/hosts
  ```
- **Kiểm chứng:**
  - `getent hosts www.lab9.test` $\rightarrow$ Trả về `10.9.0.200` (đã bị điều hướng).
  - `curl http://www.lab9.test` $\rightarrow$ Nhận trang web giả mạo từ Kali: *"LAB 9 - TRANG MÔ PHỎNG BỊ CHUYỂN HƯỚNG"*.
  - `dig @10.9.0.10 www.lab9.test` $\rightarrow$ Vẫn trả về IP gốc `172.16.6.10` vì `dig` tự mở socket UDP/53 truy vấn trực tiếp máy chủ DNS, bỏ qua thư viện resolver và tệp hosts.
- **Khôi phục:** Khôi phục tệp `/etc/hosts` từ bản sao lưu `/etc/hosts.bak`. Kết quả phân giải trở lại máy chủ hợp lệ `172.16.6.10`.

---

### 3.3. Giai đoạn 3: Task 2 - Direct DNS Spoofing (Giả mạo phản hồi trực tiếp tới Victim)
- **Nguyên lý:** Kẻ tấn công on-path trên cùng switch nội bộ (nhờ Promiscuous Mode) bắt gói truy vấn DNS từ Victim gửi tới DNS-SERVER, đọc Transaction ID và UDP Source Port, sau đó gửi một gói tin phản hồi DNS giả mạo với IP nguồn là DNS-SERVER (`10.9.0.10`) gửi thẳng tới Victim. Do phản hồi giả mạo chỉ mất ~1.8ms còn phản hồi thật từ DMZ trễ 1.5s, gói giả mạo luôn thắng cuộc đua (Race Condition).
- **Thực thi:**
  - Trên Kali: `sudo python3 dns_spoof_lab9.py --mode victim --iface eth1`
  - Trên Victim: `dig @10.9.0.10 www.external.lab9.test`
- **Kết quả:**
  - Kali log: `[LAB9] forged victim response: www.external.lab9.test. -> 10.9.0.200; txid=33460; dst=10.9.0.100:52418`
  - Victim nhận địa chỉ IP giả mạo `10.9.0.200` chỉ sau `3 msec`!
  - `curl http://www.external.lab9.test` hiển thị trang web mô phỏng của Kali.
- **Đánh giá phạm vi:** Tấn công chỉ tác động tới phiên truy vấn đơn lẻ của Victim hiện tại. Cache của DNS-SERVER hoàn toàn sạch sẽ, không ảnh hưởng tới các máy trạm khác.

---

### 3.4. Giai đoạn 4: Task 3 - DNS Cache Poisoning (Đầu độc bộ nhớ đệm BIND9 Resolver)
- **Nguyên lý:** Thay vì tấn công máy trạm riêng lẻ, kẻ tấn công nhắm trực tiếp vào máy chủ Recursive Resolver (`10.9.0.10`). Khi DNS-SERVER forward truy vấn sang Authoritative DNS (`172.16.6.20`), Kali bắt gói tin và gửi gói phản hồi giả mạo mạo danh `172.16.6.20` gửi tới `10.9.0.10` với cờ Authoritative (`AA=1`, `QR=1`), Answer `10.9.0.200` và `TTL=120s`.
- **Thực thi:**
  - Trên DNS-SERVER: Xóa sạch cache trước thử nghiệm: `sudo rndc flush`
  - Trên Kali: `sudo python3 dns_spoof_lab9.py --mode resolver --iface eth1`
  - Trên Victim: Kích hoạt truy vấn đệ quy: `dig @10.9.0.10 www.external.lab9.test`
- **Kết quả & Bằng chứng xác thực:**
  - Kali log: `[LAB9] forged resolver response: www.external.lab9.test. -> 10.9.0.200; txid=20249; dst=10.9.0.10:59142`
  - Kiểm tra bộ nhớ đệm BIND9: Trên DNS-SERVER, chạy `sudo rndc dumpdb -cache` và kiểm tra tệp `/var/cache/bind/named_dump.db`:
    ```text
    ; zone external.lab9.test/IN: (cache)
    www.external.lab9.test. 118 A 10.9.0.200
    ```
    Bản ghi giả mạo đã được ghi nhận trực tiếp vào RAM của BIND9!
  - **Kiểm chứng tính lan truyền (Persistence):** Tiến hành tắt script trên Kali (`Ctrl+C`). Từ Victim truy vấn lại `dig @10.9.0.10 www.external.lab9.test` $\rightarrow$ Vẫn nhận kết quả `10.9.0.200` với thời gian phản hồi `0 msec` (phục vụ trực tiếp từ cache BIND9)!
- **Đánh giá phạm vi:** Mọi máy tính trong mạng khi hỏi DNS-SERVER đều bị điều hướng sang trang giả mạo cho đến khi TTL 120s hết hạn hoặc quản trị viên flush cache.

---

### 3.5. Giai đoạn 5: Phân tích chuyên sâu chuỗi gói tin Wireshark
Phân tích trên giao diện `eth1` của Kali với bộ lọc `dns`:
- **Gói 1 (`0.000000s`):** Standard Query từ `10.9.0.100` $\rightarrow$ `10.9.0.10` (UDP Sport: 52418, Dport: 53, TXID: `0x4f19`).
- **Gói 2 (`+0.000812s`):** Standard Query (Forward) từ `10.9.0.10` $\rightarrow$ `172.16.6.20` (UDP Sport: 59142, Dport: 53, TXID: `0x4f19`).
- **Gói 3 (`+0.002654s` - GÓI BƠM GIẢ):** Gửi từ Kali giả mạo nguồn `172.16.6.20` $\rightarrow$ `10.9.0.10` (UDP Sport: 53, Dport: 59142, TXID: `0x4f19`, Cờ `0x8580` QR=1, AA=1, Answer: `10.9.0.200`, TTL: 120s). Về đích chỉ sau 1.8ms!
- **Gói 4 (`+0.003410s`):** DNS-SERVER chấp nhận gói giả, lưu cache và gửi Standard Query Response trả về cho Victim (`10.9.0.200`).
- **Gói 5 (`+1.503120s` - GÓI THẬT ĐẾN SAU):** Phản hồi hợp lệ từ `172.16.6.20` $\rightarrow$ `10.9.0.10` (A = `172.16.6.10`). BIND9 lập tức loại bỏ gói này vì socket và Transaction ID đã được giải phóng.

---

### 3.6. Giai đoạn 6: Quy trình dọn dẹp, khôi phục & Hardening
1. Dừng toàn bộ các script tấn công trên Kali (`dns_spoof_lab9.py`, fake web server).
2. Dừng `auth_dns_delayed.py` trên APP-TEST.
3. Flush sạch bộ nhớ đệm: `sudo rndc flush` trên DNS-SERVER và `resolvectl flush-caches` trên Victim.
4. Trả chế độ card mạng Kali từ `Allow VMs` về `Deny` (ngăn ngừa sniffing).
5. Kiểm tra phân giải xác nhận: `dig @10.9.0.10 www.external.lab9.test` $\rightarrow$ Trả về đúng địa chỉ IP hợp lệ `172.16.6.10`.

---

## 4. Giải đáp 10 câu hỏi phân tích học thuật

### Câu 1: Tại sao `/etc/hosts` có thể ảnh hưởng trình duyệt nhưng `dig @DNS-SERVER` vẫn trả kết quả DNS gốc?
- **Trả lời:** Trình duyệt web và các ứng dụng thông thường sử dụng các hàm phân giải của thư viện C chuẩn (`glibc`) như `getaddrinfo()`. Cơ chế này tuân thủ thứ tự tra cứu quy định trong `/etc/nsswitch.conf` (`hosts: files dns`), trong đó tệp cục bộ (`files` - tức `/etc/hosts`) được kiểm tra đầu tiên; nếu tìm thấy tên miền khớp, hệ thống sử dụng ngay mà không gửi truy vấn ra mạng. Ngược lại, công cụ `dig` là tiện ích chẩn đoán DNS chuyên biệt, không sử dụng thư viện resolver hệ thống hay tệp `/etc/hosts`, mà tự tạo socket UDP/TCP trực tiếp tới địa chỉ IP của máy chủ DNS được chỉ định sau `@` để truy vấn trực tiếp cơ sở dữ liệu trên máy chủ đó. Do đó `dig` luôn phản ánh dữ liệu gốc trên DNS Server.

### Câu 2: Những trường nào của DNS/UDP phải khớp để một phản hồi giả có cơ hội được chấp nhận?
- **Trả lời:** Các trường bắt buộc phải khớp tuyệt đối gồm:
  1. *IP Nguồn:* Phải là IP đích mà bên gửi truy vấn đã gửi tới (IP của DNS Server đối với Victim, hoặc IP của Authoritative Server đối với Resolver).
  2. *IP Đích:* Phải là IP của thiết bị đã phát truy vấn.
  3. *Giao thức:* UDP (Protocol 17).
  4. *UDP Source Port:* Cổng 53.
  5. *UDP Destination Port:* Khớp chính xác với cổng nguồn tạm (ephemeral port) mà bên gửi truy vấn đã mở.
  6. *DNS Transaction ID:* Chuỗi 16-bit ID trong DNS Header phải trùng khớp hoàn toàn với Transaction ID ban đầu.
  7. *Question Section:* QNAME, QTYPE và QCLASS phải khớp nguyên vẹn với câu hỏi.
  8. *DNS Flags:* QR=1 (Response), RCODE=0 (No error), và các cờ AA/RA phù hợp.
  9. *Yếu tố thời gian (Race condition):* Gói phản hồi giả phải đến đích TRƯỚC phản hồi hợp lệ.

### Câu 3: Tại sao Task 2 chỉ ảnh hưởng Victim hiện tại, trong khi Task 3 có thể ảnh hưởng nhiều client dùng cùng resolver?
- **Trả lời:** Trong Task 2 (Direct DNS Spoofing), gói phản hồi giả mạo được gửi trực tiếp tới cổng socket của một máy Victim cụ thể và chỉ được xử lý bởi ngăn xếp mạng của riêng máy đó; DNS-SERVER hoàn toàn không nhận gói tin này nên bộ nhớ đệm không hề bị ảnh hưởng. Trong khi đó ở Task 3 (DNS Cache Poisoning), đối tượng tiếp nhận gói tin giả mạo chính là máy chủ BIND9 Resolver. Khi Resolver chấp nhận gói tin giả, nó lưu bản ghi độc hại vào bộ nhớ đệm dùng chung (Shared Cache) với thời gian TTL quy định. Kể từ đó, bất kỳ máy trạm nào trong toàn mạng gửi truy vấn cùng tên miền đều được Resolver trả lời ngay lập tức bằng dữ liệu giả mạo từ cache mà không cần truy vấn ra ngoài.

### Câu 4: Vai trò của TTL (Time-To-Live) trong cache poisoning là gì?
- **Trả lời:** TTL quy định khoảng thời gian (tính bằng giây) mà máy chủ đệm được phép lưu trữ và tái sử dụng bản ghi trước khi phải xóa đi để truy vấn lại. Trong tấn công Cache Poisoning, vai trò của TTL mang tính quyết định:
  1. *Duy trì tính bền vững (Persistence):* TTL càng lớn thì bản ghi giả mạo tồn tại trong cache của DNS Server càng lâu mà kẻ tấn công không cần phải gửi thêm gói tin giả mạo.
  2. *Giảm thiểu nguy cơ bị phát hiện:* Trong thời gian TTL còn hiệu lực, Resolver không gửi truy vấn ra Authoritative Server thật, giảm lưu lượng bất thường và tránh kích hoạt cảnh báo IDS/IPS.
  3. *Cửa sổ tác động:* Toàn bộ người dùng trong mạng sẽ tiếp tục bị điều hướng sang trang độc hại cho tới khi TTL hết hạn hoặc quản trị viên can thiệp thủ công (`rndc flush`).

### Câu 5: Tại sao VirtualBox Promiscuous Mode = Allow VMs cần thiết trong bài này?
- **Trả lời:** Mạng nội bộ ảo "Internal Network" của VirtualBox mô phỏng hoạt động của một thiết bị chuyển mạch lớp 2 (L2 Switch). Switch thông thường chỉ chuyển tiếp khung tin Unicast trực tiếp tới đúng cổng nối với card mạng có địa chỉ MAC đích. Card mạng của Kali có MAC khác với Victim và DNS-SERVER. Nếu ở chế độ thông thường (Deny), switch ảo sẽ loại bỏ và không gửi các gói tin Unicast giữa Victim và DNS-SERVER tới Kali. Khi cấu hình `Promiscuous Mode = Allow VMs`, switch ảo VirtualBox cho phép card mạng của Kali nhận toàn bộ lưu lượng mạng truyền qua switch giữa tất cả các máy ảo trong cùng phân đoạn (tương tự tính năng Port Mirroring / SPAN). Nhờ đó, Scapy mới có thể "ngửi" (sniff) được gói truy vấn DNS trong thời gian thực, đọc Transaction ID và cổng nguồn để thực hiện tấn công on-path spoofing.

### Câu 6: Vì sao LAB dùng mạng DNSLAB riêng thay vì tấn công trực tiếp DC01 DNS của LAN-DOMAIN?
- **Trả lời:**
  1. *Nguyên tắc cô lập an toàn (Blast Radius):* DC01 là máy chủ Domain Controller Active Directory đóng vai trò cốt lõi trong việc xác thực người dùng, dịch vụ Kerberos, Group Policy và định giải tên miền cho toàn bộ hệ thống lab. Can thiệp hoặc đầu độc DC01 có thể làm sập xác thực miền, hỏng cấu hình và gián đoạn toàn bộ các bài lab khác.
  2. *Kiểm soát biến số thí nghiệm:* Mạng DNSLAB riêng cho phép tinh chỉnh các tham số BIND9 (như vô hiệu hóa tạm thời DNS Cookie) và điều chỉnh độ trễ phân giải độc lập, giúp tái lập kịch bản tấn công on-path mang tính xác định cao.
  3. *Ngăn ngừa rò rỉ lưu lượng:* Đảm bảo các gói tin thô giả mạo (raw packet spoofing) được cô lập phía sau pfSense, không rò rỉ ra mạng thật của trường hay Internet.

### Câu 7: Khác nhau giữa authoritative DNS, recursive resolver và caching resolver?
- **Trả lời:**
  - *Authoritative DNS Server:* Là máy chủ nắm giữ tệp cơ sở dữ liệu gốc (zone file) chứa các bản ghi chính thức (SOA, NS, A, MX) cho một tên miền cụ thể. Nó chỉ trả lời các câu hỏi về tên miền mà nó được ủy quyền quản lý, không bao giờ đi hỏi máy chủ khác thay cho client.
  - *Recursive Resolver:* Là máy chủ nhận truy vấn từ client và thay mặt client thực hiện toàn bộ quy trình tra cứu đệ quy qua các cấp máy chủ (Root $\rightarrow$ TLD $\rightarrow$ Authoritative) cho đến khi tìm được câu trả lời cuối cùng để trả lại cho client.
  - *Caching Resolver:* Là chức năng lưu trữ tạm thời các kết quả phân giải DNS đã thu thập vào bộ nhớ RAM trong thời gian TTL. Khi có truy vấn mới cho cùng tên miền, Caching Resolver trả lời ngay từ bộ nhớ đệm mà không cần lặp lại quy trình đệ quy ra bên ngoài.

### Câu 8: DNSSEC giải quyết vấn đề gì và vì sao zone `.test` unsigned trong LAB không tự được bảo vệ?
- **Trả lời:**
  - *Vấn đề DNSSEC giải quyết:* DNSSEC (DNS Security Extensions) bổ sung cơ chế xác thực nguồn gốc dữ liệu (Data Origin Authentication) và bảo vệ tính toàn vẹn (Data Integrity) thông qua mật mã khóa công khai. Các bản ghi DNS được ký số (RRSIG). Resolver sử dụng khóa công khai (DNSKEY) và chuỗi tin cậy (Chain of Trust) để xác minh chữ ký. Nếu gói phản hồi bị giả mạo, chữ ký không hợp lệ và Resolver sẽ hủy bỏ gói tin, trả về mã lỗi `SERVFAIL`, ngăn chặn hoàn toàn tấn công giả mạo và đầu độc cache.
  - *Vì sao zone `.test` trong bài không tự bảo vệ được:* Zone `lab9.test` và `external.lab9.test` là các vùng thử nghiệm nội bộ chưa được ký số (Unsigned Zones). Chúng hoàn toàn không có các bản ghi khóa bảo mật DNSKEY hay chữ ký RRSIG. Khi gặp vùng chưa ký số (Insecure Delegation), BIND9 dù có cấu hình `dnssec-validation auto;` vẫn tự động lùi về chế độ xử lý DNS truyền thống không kiểm tra chữ ký. Do đó, gói tin giả mạo có Transaction ID và cổng khớp vẫn được BIND9 chấp nhận.

### Câu 9: Tại sao chỉ chặn UDP/53 là chưa đủ nếu muốn kiểm soát DNS trong mạng hiện đại?
- **Trả lời:**
  1. *DNS over TCP (TCP/53):* DNS chuyển sang TCP/53 khi kích thước gói tin vượt quá giới hạn UDP (512 bytes / EDNS0) hoặc khi thực hiện Zone Transfer. Kẻ tấn công có thể dùng TCP/53 để vượt qua bộ lọc chỉ chặn UDP.
  2. *DNS over TLS (DoT - RFC 7858):* Toàn bộ truy vấn DNS được mã hóa bên trong đường hầm TLS trên cổng TCP 853, tường lửa L3/L4 không thể kiểm tra nội dung.
  3. *DNS over HTTPS (DoH - RFC 8484):* Truy vấn DNS được đóng gói bên trong các yêu cầu HTTPS qua cổng TCP 443 (cùng cổng với web an toàn thông thường). Tường lửa thông thường không thể phân biệt giữa lướt web HTTPS và truy vấn DoH nếu không có giải pháp SSL Decryption/DPI.
  4. *DNS over QUIC (DoQ - RFC 9250):* Sử dụng giao thức UDP cổng 853 kết hợp mã hóa TLS 1.3, đem lại tốc độ cao và khả năng lẩn tránh mạnh mẽ.
  5. *DNS Tunneling:* Mã độc có thể mã hóa dữ liệu đánh cắp hoặc lệnh điều khiển giấu bên trong các subdomain của truy vấn DNS thông thường để lọt qua các cổng mạng tiêu chuẩn.

### Câu 10: Nêu tối thiểu bốn biện pháp hardening sau khi hoàn thành bài.
- **Trả lời:**
  1. *Kích hoạt và bắt buộc DNS COOKIE (RFC 7873 / RFC 9018):* Xóa bỏ cấu hình ngoại lệ `send-cookie no;` trong BIND9. Cơ chế DNS Cookie trao đổi mã xác thực mật mã 64-bit hai chiều giữa Client và Server, vô hiệu hóa khả năng tiêm gói tin giả mạo của kẻ tấn công on-path hoặc off-path.
  2. *Triển khai DNSSEC toàn diện:* Ký số cho toàn bộ các zone nội bộ và bật xác thực `dnssec-validation auto;` trên các Resolver, đảm bảo mọi bản ghi đều có chữ ký số mật mã hợp lệ.
  3. *Phân đoạn mạng và An ninh chuyển mạch L2 (L2 Switch Security):* Tách rời Client và Server vào các VLAN riêng biệt. Trên switch, kích hoạt Dynamic ARP Inspection (DAI), DHCP Snooping, Port Security và Private VLAN (PVLAN) nhằm triệt tiêu hoàn toàn khả năng nghe lén Promiscuous Sniffing và ARP Spoofing.
  4. *Kiểm soát luồng DNS Egress trên Firewall pfSense:* Cấu hình luật tường lửa chỉ cho phép DUY NHẤT IP của máy chủ DNS nội bộ được gửi gói tin ra cổng 53 (UDP/TCP) ra Internet. Chặn tuyệt đối (Block + Log) mọi truy vấn cổng 53 trực tiếp từ các máy trạm, buộc mọi thiết bị phải đi qua DNS Resolver được kiểm soát.
  5. *Ngẫu nhiên hóa toàn diện cổng nguồn UDP (Source Port Randomization):* Kết hợp ngẫu nhiên hóa Transaction ID 16-bit và cổng nguồn UDP (14-16 bit entropy) để mở rộng không gian tìm kiếm lên tới 32-bit (~4.3 tỷ trạng thái), loại bỏ khả năng tấn công đoán mò (Kaminsky attack).

---

## 5. Kết luận bài học và Đề xuất giải pháp an ninh

1. **Đánh giá kết quả thực hành:**
   - Hoàn thành xuất sắc 100% các mục tiêu bài thực hành Lab 8.
   - Nắm vững cơ chế hoạt động tầng thấp của giao thức DNS, vai trò của các trường tiêu đề (Transaction ID, UDP Port, Flags) và điểm yếu cố hữu của giao thức UDP không trạng thái.
   - Tái lập thành công kỹ thuật tấn công chuyển hướng tệp `/etc/hosts`, tấn công giả mạo phản hồi trực tiếp (Direct DNS Spoofing) và tấn công đầu độc bộ nhớ đệm (DNS Cache Poisoning).
   - Phân tích cặn kẽ chuỗi 5 gói tin trên Wireshark, giải thích bản chất cuộc đua gói tin (Race Condition).

2. **Đề xuất chiến lược phòng thủ theo chiều sâu (Defense-in-Depth):**
   - Không dựa vào một cơ chế bảo vệ duy nhất; cần kết hợp đồng bộ giữa **Mật mã học** (DNSSEC, DNS Cookie), **Phân đoạn mạng L2/L3** (VLAN, pfSense Firewall Policy, Port Security) và **Kiểm soát dịch vụ DNS tập trung** (Egress Filtering, DoH/DoT Monitoring).
   - Duy trì quy trình kiểm tra toàn vẹn định kỳ đối với cấu hình máy chủ DNS và nhật ký truy vấn để kịp thời phát hiện các dấu hiệu bất thường trong hệ thống mạng doanh nghiệp.

---
*Báo cáo được thực hiện và hoàn thành bởi sinh viên Đặng Minh Nhật - MSSV: 1150080029 - Lớp: 11DHCNPM1.*
