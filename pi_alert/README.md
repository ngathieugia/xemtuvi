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

### Chạy 24/7
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
