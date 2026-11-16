# 🤖 Bot cảnh báo giá Pi Network (PI/USDT) qua Telegram

Theo dõi giá PI liên tục (mặc định: hợp đồng vĩnh cửu **PIUSDT Perpetual** trên OKX, tự chuyển sang Bitget / MEXC / Gate nếu sàn lỗi), tính chỉ báo kỹ thuật và gửi cảnh báo quan trọng về Telegram.

## Bot cảnh báo những gì?

| # | Sự kiện | Mức |
|---|---------|-----|
| 1 | Giá tăng/giảm mạnh trong 15 phút / 1 giờ / 24 giờ (ngưỡng % tự đặt) | 🚨 |
| 2 | Giá cắt qua các mốc bạn đặt (VD: 0.11, 0.12) | ⚠️ |
| 3 | **UT Bot Alerts** (Key=2, ATR=1) báo MUA/BÁN ở khung tín hiệu và khung lớn | ⚠️/🚨 |
| 4 | **Step Channel Momentum Trend** (3; 0.6) đổi xu hướng TĂNG/GIẢM | ⚠️ |
| 5 | RSI vào vùng quá bán (<30) / quá mua (>70) | ⚠️ |
| 6 | Khối lượng đột biến (gấp 3 lần trung bình) | ⚠️ |
| 7 | Giá phá dải Bollinger | ℹ️ |
| 8 | Funding rate cực đoan (thị trường phái sinh quá lệch một phía) | ⚠️ |
| 9 | **Điểm cơ hội mua** chuyển sang vùng thuận lợi (≥70/100) | 🚨 |

Thêm vào đó, cứ mỗi `SUMMARY_HOURS` giờ bot gửi **báo cáo tổng hợp**: giá, chỉ báo, hỗ trợ/kháng cự, điểm cơ hội và kế hoạch mua chia phần tham khảo.

Lệnh chat với bot: `/gia`, `/phantich`, `/help`.

> Về 2 chỉ báo trong ảnh TradingView: UT Bot được cài đúng công thức gốc (ATR Trailing Stop). Step Channel Momentum Trend của ChartPrime là script đóng, ở đây là **bản mô phỏng** theo cùng ý tưởng (đường giữa bậc thang từ pivot, kênh ± ATR×0.6), nên giá trị có thể lệch nhẹ so với TradingView.

## 🖥️ Dashboard web (React + Vite)

Giao diện xem giá trực tiếp tại **`https://tenmien-cua-ban.com/pi/app/`**. Nếu app Python nằm trong thư mục con, thêm thư mục đó vào trước `/pi/app/`.

Dashboard gồm:
- Giá hiện tại, % thay đổi 15p / 1h / 24h, vị trí giá trong biên độ 24h, khối lượng, funding.
- **Đồng hồ điểm cơ hội mua** kèm lý do cộng/trừ điểm.
- **Biểu đồ nến** với đường UT Bot (mũi tên Mua/Bán), kênh Step Channel, EMA, Bollinger, khối lượng, khung RSI. Có thể bật/tắt từng lớp.
- Chọn khung thời gian 5m / 15m / 1h / 4h / 1d. Tự làm mới mỗi 30 giây.
- Bảng chỉ báo hai khung, thang hỗ trợ/kháng cự, kế hoạch mua chia phần.

Thêm `?demo=1` vào cuối địa chỉ để xem bằng dữ liệu giả lập.

**Không cần Node.js trên hosting:** bản build sẵn nằm trong `pi_alert/dashboard_dist/`, Flask tự phục vụ.

Muốn sửa giao diện thì sửa mã nguồn trong `dashboard/` trên máy tính:
```bash
cd dashboard && npm install
python -m pi_alert.web     # cửa sổ 1: API ở cổng 5000
npm run dev                # cửa sổ 2: mở http://localhost:5173/?demo=1
npm run build              # build lại vào pi_alert/dashboard_dist rồi tải lên hosting
```

Dashboard chỉ để **xem**. Còn **cảnh báo Telegram** do bot Python gửi (qua Cron), nên vẫn chạy kể cả khi không ai mở trang.

## Cài đặt (5 phút)

1. **Tạo bot**: mở Telegram, chat với `@BotFather` → `/newbot` → lấy **token**.
2. **Cài Python 3.9+**, rồi tại thư mục gốc dự án:
   ```bash
   pip install -r pi_alert/requirements.txt
   cp pi_alert/.env.example pi_alert/.env
   ```
3. Điền `TELEGRAM_BOT_TOKEN` vào `pi_alert/.env`. Nhắn `/start` cho bot, rồi chạy:
   ```bash
   python -m pi_alert.main --get-chat-id
   ```
   Chép `chat_id` hiện ra vào `TELEGRAM_CHAT_ID`.
4. Chạy thử không cần mạng: `python -m pi_alert.main --demo`
5. Gửi 1 báo cáo thật: `python -m pi_alert.main --report`
6. Chạy liên tục: `python -m pi_alert.main`

### 🌐 Chạy trên hosting cPanel ("Setup Python App")

Hosting cPanel chỉ chạy code khi có người truy cập, không giữ được chương trình chạy liên tục. Vì vậy bot chia làm 2 phần:
- **Cron Job**: quét giá và gửi cảnh báo mỗi 1–2 phút.
- **Webhook**: Telegram gọi vào website mỗi khi bạn nhắn `/gia`, `/phantich`.

**Bước 1 – Tải code lên.** Đưa cả thư mục dự án (gồm `server.py`, `lasotuvi/`, `pi_alert/`) lên hosting, VD `/home/USER/xemtuvi`.

**Bước 2 – Python App.** Vào cPanel → *Setup Python App*:
- Nếu **đã có app tử vi** dùng `server.py`: giữ nguyên. Bot đã gắn sẵn vào app này ở đường dẫn `/pi/...`.
- Nếu muốn **app riêng**: *Create Application* → Python 3.9+ → *Application root* `xemtuvi` → *Application URL* tùy chọn → *Application startup file* `pi_alert_wsgi.py` → *Entry point* `application`.

Ở mục *Configuration files* nhập `requirements.txt` → bấm **Run Pip Install**. Chép lệnh *"Enter to the virtual environment"* hiển thị ở đầu trang (dạng `source /home/USER/virtualenv/xemtuvi/3.x/bin/activate && cd /home/USER/xemtuvi`).

**Bước 3 – Cấu hình.** Vào *File Manager* → `xemtuvi/pi_alert/` → copy `.env.example` thành `.env`, rồi điền:
- `TELEGRAM_BOT_TOKEN`: token lấy từ @BotFather;
- `WEBHOOK_SECRET`: chuỗi bí mật tự đặt, VD `PiBot_8x2kq9`;
- `DRY_RUN=0`.

Bấm **Restart** app.

**Bước 4 – Đăng ký webhook.** Mở *Terminal* trong cPanel, dán lệnh *Enter to the virtual environment*, rồi chạy:
```bash
python -m pi_alert.main --set-webhook https://tenmien-cua-ban.com
```
Nếu app nằm ở đường dẫn con, thêm đường dẫn đó vào sau tên miền (VD `https://tenmien.com/tuvi`). Nhắn `/start` cho bot: bot trả lời **chat_id** của bạn. Điền vào `TELEGRAM_CHAT_ID` trong `.env` → **Restart** app. Nhắn `/gia` để thử.

**Bước 5 – Cron Job quét giá.** cPanel → *Cron Jobs* → chọn *Once Per Minute* (hoặc `*/2`), lệnh:
```bash
cd /home/USER/xemtuvi && /home/USER/virtualenv/xemtuvi/3.x/bin/python -m pi_alert.main --once >> pi_alert/cron.log 2>&1
```
Thay `USER` và `3.x` theo đường dẫn thật trong lệnh *Enter to the virtual environment*. Bot có khóa file nên cron chạy chồng nhau cũng không gửi trùng.

> Hosting **không có Cron Jobs**: đặt `CRON_SECRET` trong `.env`, rồi tạo tác vụ miễn phí trên cron-job.org gọi `https://tenmien.com/pi/cron?key=CRON_SECRET` mỗi 1–2 phút.

**Kiểm tra:**
- Mở `https://tenmien.com/pi/` → thấy `"ok": true`.
- Xem lỗi trong `pi_alert/cron.log` và `stderr.log` của app.
- Nếu một sàn bị chặn từ hosting, bot tự chuyển sang sàn khác. Cũng có thể đặt `EXCHANGE=gate` hoặc `mexc`.

### Chạy 24/7 trên VPS / máy tính
- **Máy chủ Linux / VPS** (`systemd`): tạo `/etc/systemd/system/pi-alert.service`
  ```ini
  [Service]
  WorkingDirectory=/duong/dan/xemtuvi
  ExecStart=/usr/bin/python3 -m pi_alert.main
  Restart=always
  [Install]
  WantedBy=multi-user.target
  ```
  rồi `systemctl enable --now pi-alert`.
- **Điện thoại Android**: cài Termux → `pkg install python git` → clone dự án và chạy như trên (bật "Acquire wakelock").
- **Cron** (không cần chạy nền): `*/2 * * * * cd /duong/dan/xemtuvi && python3 -m pi_alert.main --once`

Kiểm thử: `python -m unittest discover -s pi_alert/tests -t .`

## Điểm cơ hội mua (0–100) được tính thế nào?

Bắt đầu từ 50 rồi cộng/trừ:

- **Xu hướng lớn (4h)**: giá > EMA50 > EMA200 (+10) hoặc ngược lại (−10); Step Channel 4h tăng/giảm (±5).
- **Tín hiệu (15m)**: UT Bot đang MUA/BÁN (±8); Step Channel (±5); MACD động lượng (±4).
- **Vùng giá – mua rẻ, không mua đuổi**: RSI 4h quá bán (+12) / quá mua (−15); RSI 15m nóng (−10); chạm Bollinger dưới (+6) / trên (−6); giá ở 25% đáy biên độ 60 ngày (+8) / 20% đỉnh (−8); sát hỗ trợ (+5).
- **Funding**: âm (+4, phe bán đông dễ bị ép), dương cao (−4).

| Điểm | Ý nghĩa |
|------|---------|
| ≥ 70 | 🟢 Thuận lợi – mua rải từng phần, đặt cắt lỗ dưới hỗ trợ |
| 55–69 | 🟡 Khá – mua thăm dò lượng nhỏ |
| 40–54 | ⚪ Trung tính – quan sát |
| < 40 | 🔴 Bất lợi – đứng ngoài |

## Nguyên tắc mua PI hợp lý (tham khảo)

1. **Không mua đuổi** khi vừa nhận cảnh báo "🚀 TĂNG MẠNH" + RSI quá mua. Chờ giá điều chỉnh về hỗ trợ / trailing stop UT Bot.
2. **Thời điểm đẹp** thường là khi *đồng thời*: giá về vùng hỗ trợ khung ngày, RSI 4h thấp (<40), rồi UT Bot 15m/4h bật **MUA** và Step Channel chuyển **TĂNG** (xác nhận đảo chiều).
3. **Chia vốn 3 phần (DCA)** theo kế hoạch bot gợi ý (30% – 30% – 40%), không dồn hết một lần.
4. **Luôn có điểm cắt lỗ**: đóng cửa ngày thủng hỗ trợ cuối cùng ≈ −6% thì dừng lại.
5. **Không dùng đòn bẩy cao** trên hợp đồng vĩnh cửu; PI biến động mạnh, thanh khoản tập trung ở ít sàn, có rủi ro mở khóa token.
6. Theo dõi thêm tin tức (mở khóa token, niêm yết sàn mới, cập nhật Mainnet) – bot chỉ đọc giá, không đọc tin.

> ⚠️ Mọi thông tin chỉ mang tính tham khảo kỹ thuật, không phải khuyến nghị đầu tư. Tài sản số có rủi ro mất vốn cao.
