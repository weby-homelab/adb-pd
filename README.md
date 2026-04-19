# 🛡️ ADB-PD (Private DNS Adblock)
**High-performance, modern DNS-over-HTTPS/TLS/QUIC resolver with a pro-grade Glassmorphism Dashboard.**

---

## 🌍 Overview / Огляд

**ADB-PD** is a lightweight, self-hosted DNS solution designed for privacy, speed, and absolute control. Unlike traditional resolvers, ADB-PD focuses on modern encrypted protocols and providing a real-time, aesthetically pleasing management experience.

**ADB-PD** — це легке, приватне DNS-рішення, створене для максимальної швидкості та повного контролю. На відміну від застарілих систем, ADB-PD фокусується на сучасних зашифрованих протоколах та надає зручний інтерфейс у стилі Glassmorphism для керування вашою мережею.

---

## ✨ Key Features / Ключові можливості

### 🚀 Performance & Logic
- **Parallel Upstream Resolution:** Queries multiple DNS providers simultaneously (Google, Cloudflare, Quad9) and returns the fastest response. No more DNS lag.
- **Conditional DNS Routing:** Route specific domains to specific servers (e.g., `[/youtube.com/]https://dns.google/dns-query`).
- **Optimistic Caching:** Serves expired records from cache while updating them in the background.

### 🔒 Security & Privacy
- **Encrypted Protocols:** Native support for **DoH (HTTP/2)**, **DoT (TLS 853)**, and **Plain DNS (UDP/TCP)**.
- **Robust ACL:** Access Control Lists based on IP, CIDR, or unique Client IDs (SNI-based for DoT).
- **Stealth Mode:** Unauthorized clients are dropped (timeout) instead of rejected, hiding your server from scanners.

### 🎨 Pro-Dashboard
- **Glassmorphism UI:** A modern, blur-heavy SPA dashboard.
- **Live Query Logs:** Real-time stream with response IPs, processing time, and rule attribution.
- **Visual Analytics:** Interactive activity charts and top statistics.

---

## 🛠 Tech Stack / Стек технологій
- **Backend:** Python 3.12 (FastAPI, Hypercorn, DNslib)
- **Frontend:** Vanilla HTML5 / Tailwind-inspired CSS / Chart.js
- **Container:** Docker (Debian-slim)

---

## 🚀 Quick Start / Швидкий старт

### Using Docker (Recommended)
```bash
docker run -d --name adb-pd \
  --network host \
  -v /path/to/config.yaml:/app/config.yaml \
  -v /etc/letsencrypt:/etc/letsencrypt:ro \
  -v /var/log/adb-pd.log:/var/log/dna-admin.log \
  --restart always \
  addmax/adb-pd:latest
```

---

## 📝 Configuration / Налаштування

Copy `app/config.yaml.example` to `app/config.yaml` and update your TLS paths:
```yaml
tls:
  enabled: true
  server_name: "your-domain.com"
  certificate_path: "/etc/letsencrypt/live/your-domain.com/fullchain.pem"
  private_key_path: "/etc/letsencrypt/live/your-domain.com/privkey.pem"
```

---

## 🤝 Contribution
Developed with ❤️ by **AddMax**. Feel free to fork and PR!

---

## 📜 License
MIT License. Free for personal and commercial use.
