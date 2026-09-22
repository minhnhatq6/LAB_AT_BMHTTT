# BÁO CÁO THỰC HÀNH LAB 3: NHẬN DIỆN VÀ ỨNG PHÓ CÁC MỐI ĐE DỌA ATTT

## 1. Thông tin sinh viên
- Họ và tên: Đặng Minh Nhật
- MSSV: 11500080029
- Tên bài Lab: Lab 3 - Nhận diện và ứng phó các mối đe dọa đến an toàn thông tin
- Môi trường: Windows 10 x64 (Máy thật)
- Đường dẫn thực hành: `E:\ANTOANMANG\LAB3`

## 2. Cách dựng môi trường
1. Tạo cấu trúc thư mục `Evidence`, `Tools`, `Downloads`, `Assets` tại `E:\ANTOANMANG\LAB3`.
2. Tải và giải nén các công cụ Sysinternals (Sysmon 15.22, Autoruns 14.3, Process Explorer 17.14).
3. Cài đặt môi trường Python và Wireshark kèm Npcap.
4. Cấu hình Sysmon với file rule `sysmon-lab.xml` đi kèm bài lab.

## 3. Các tình huống đã thực hiện & Kết quả
| Tình huống | Mô tả nội dung | Kết quả |
| :--- | :--- | :---: |
| **B.0** | Thu thập Baseline hệ thống (OS, Defender, Firewall, Process) | **PASS** |
| **TH1** | Phân loại Tài sản, Lỗ hổng, Mối đe dọa, Rủi ro và 5 nguồn đe dọa | **PASS** |
| **TH2** | Kiểm chứng cơ chế Real-time Protection của Defender bằng chuỗi EICAR | **PASS** |
| **TH3** | Sinh sự kiện xác thực (4624/4625/4648), phát hiện brute force & đổi mật khẩu | **PASS** |
| **TH4** | Nhận diện Persistence (Run key, Task) và giám sát listener cục bộ 8080 | **PASS** |
| **TH5** | Sniffing Wireshark: so sánh lưu lượng Plaintext HTTP và mã hóa TLS/HTTPS | **PASS** |
| **TH6** | Kiểm thử tải nội bộ DoS và phân tích log phân tán DDoS, Mail bombing | **PASS** |
| **TH7** | Phân tích mẫu email Phishing offline và nhận diện các kỹ thuật Social Engineering | **PASS** |
| **B.8** | Dọn dẹp artefact (Cleanup) và băm SHA-256 toàn bộ bằng chứng Evidence | **PASS** |

## 4. Lỗi gặp phải và cách khắc phục
- Vấn đề:Khi ghi file `eicar.com.txt`, lệnh PowerShell có thể ném exception `UnauthorizedAccessException`.
	- Khắc phục: Đây là hành vi đúng mong đợi vì Microsoft Defender đã phát hiện và khóa quyền ghi file ngay lập tức; sử dụng khối `try { ... } catch { ... }` để ghi log lỗi mà không ngắt kịch bản.
- Vấn đề: Thực hiện trên máy thật không có tính năng Revert Snapshot.
	- Khắc phục: Thực hiện nghiêm ngặt quy trình Cleanup ở Bước 8, xóa thủ công Run key, Scheduled Task, dừng tiến trình port 8080 và xóa tài khoản `lab3user`, sau đó đối chiếu lại diff của Autoruns.
- Vấn đề: Thực hiện trên máy thật Windows 10 có cấu hình hệ thống tắt Defender sâu trong kernel dịch vụ nên lệnh Get-MpComputerStatus trả về False.   
	- Khắc phục: Đã dọn dẹp sạch toàn bộ artefact nguy hại của bài lab; cập nhật lại khóa registry WinDefend và giải trình rõ sự khác biệt giữa môi trường máy trạm vật lý và máy ảo tiêu chuẩn.   