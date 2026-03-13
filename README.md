# 🚀 Comarai Algo ProMax: XAUUSD Trading Indicator
> *Tích hợp 3 sức mạnh: Smart Money Concepts (SMC) + Trend Filters (MA) + M.L. Proxy Triggers.*

[![Pine Script](https://img.shields.io/badge/Pine%20Script-v5-green)](https://www.tradingview.com/pine-script-docs/)
[![Comarai](https://img.shields.io/badge/By-Comarai-purple)](https://comarai.com)

---

## 💡 Tư Duy Phát Triển (The Philosophy)

Một chỉ báo tốt không phải là một chỉ báo hiển thị BÁN/MUA ngẫu nhiên. Nó phải kết hợp được các yếu tố phân tích kỹ thuật cốt lõi:
1. **Trend (Xu hướng lớn):** Lọc theo đường EMA 200 để tránh giao dịch ngược bão.
2. **Context (Cấu trúc thị trường):** Tìm kiếm các Key Levels quan trọng như **Order Blocks (OB)**, **Market Structure Breaks (MSB)**, và **Fair Value Gaps (FVG)**. Mọi thứ đều được code từ nguồn tham khảo Github của _hungpixi/xauusd-smc-signal-engine_.
3. **Trigger (Điểm vào lệnh tối ưu):** Thay vì vào lệnh ngay lập tức lỏng lẻo, thuật toán sẽ chờ giá xuất hiện FVG gần nhất và một tín hiệu Pullback của Momentum (RSI Overbought/Oversold Proxy ML Trigger).

## 📊 Backtest (Python & XGBoost)
Kèm theo dự án Pine Script là framework Backtesting bằng Python **(XGBoost + Smart Money Concepts)**. Test trên dữ liệu 15 phút của vàng (`XAUUSD_M15.csv`) đã cho **Winrate ~49%** và tỷ lệ **EV dương (+0.223R / lệnh)** (Test set split). Hệ thống sử dụng *Structural Stop Losses* (dựa trên Swing High/Low) thay vì ATR cứng nhắc để tránh bị nhiễu.

## 🚀 Trải Nghiệm Chỉ Báo Trực Quan
- **UI/UX Tối Ưu:** Các vùng OB, FVG được làm mượt mà, mờ ảo (transparent) tránh che khuất mắt người dùng, theo chuẩn "Medium Brightness".
- **Real-time Alert JSON:** Sẵn sàng kết nối vào framework Automation của comarai (n8n, webhook).

---

## 👨‍💻 Tác Giả

**Phạm Phú Nguyễn Hưng** — Freelancer, Trader nghiệp dư, AI Automation Builder 
Dự án được xây dựng dưới định hướng kết hợp Trading thực chiến và khả năng Automation AI. Code là AI phụ trợ nhưng tư duy lắp ghép các feature XGBoost + SMC là của người giao dịch.

---

## 🤝 Bạn Muốn Hệ Thống Trading/AI Tương Tự?

### Bạn Cần → Chúng Tôi Đã Làm ✅

| Bạn Cần | Chúng Tôi Đã Làm |
|---------|-----------------|
| Thiết kế bộ Trading View indicator tùy chỉnh | ✅ Comarai Algo ProMax (PineScript v5) |
| Backtest bằng Data khoa học Python | ✅ VectorBT/Pandas framework siêu tốc |
| Mở khóa Sức Mạnh Machine Learning | ✅ XGBoost & KNN Signal Engines |
| Xây dựng Bot Giao Dịch Tự Động MT5 | ✅ MQL5 EA (Có Risk Management) |
| Tối giản mô hình làm vệc (AI Agency) | ✅ Hệ sinh thái Comarai Automation |

### 🚀 Liên Hệ Ngay

<div align="center">

[![Demo](https://img.shields.io/badge/🌐_Yêu_Cầu_Demo-comarai.com-purple?style=for-the-badge)](https://comarai.com)
[![Zalo](https://img.shields.io/badge/💬_Zalo-0834422439-blue?style=for-the-badge)](https://zalo.me/0834422439)
[![Email](https://img.shields.io/badge/📧_Email-hungphamphunguyen%40gmail.com-red?style=for-the-badge)](mailto:hungphamphunguyen@gmail.com)

</div>

---

### 🤖 Về Comarai — *Companion for Marketing & AI Automation*

> *"Thay vì thuê 5 nhân viên, tôi chạy 4 AI agent 24/7 với chi phí thấp hơn 90%. "*
> — Nguyễn Hưng

**Đội ngũ AI của chúng tôi:**
- 🤖 **Em Sale** — Tự động outreach tìm kiếm deal.
- ✍️ **Em Content** — Tạo bài viết cho kênh Tiktok "Kẻ Lười Chăm Chỉ".
- 📣 **Em Marketing** — Optimize Ad campaigns.
- 📈 **Em Trade** — Build chỉ báo (giống như Repo này) và trade quản trị Quỹ.

**[comarai.com](https://comarai.com)** | **[github.com/hungpixi](https://github.com/hungpixi)**
