# 🛡️ ADB-PD (Private DNS Adblock)
**High-performance DNS-over-HTTPS/TLS/QUIC resolver with a pro-grade Glassmorphism Dashboard.**

[![Docker Image Size](https://img.shields.io/docker/image-size/webyhomelab/adb-pd/latest)](https://hub.docker.com/r/webyhomelab/adb-pd)
[![Docker Pulls](https://img.shields.io/docker/pulls/webyhomelab/adb-pd)](https://hub.docker.com/r/webyhomelab/adb-pd)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌍 Overview / Огляд

**ADB-PD** is a lightweight, self-hosted DNS solution designed for privacy, speed, and absolute control. It serves as a modern alternative to legacy DNS servers, focusing on encrypted protocols (DoH, DoT) and providing a real-time, aesthetically pleasing management experience.

**ADB-PD** — це легке, приватне DNS-рішення, створене для максимальної швидкості та повного контролю. Це сучасна альтернатива застарілим DNS-серверам, яка фокусується на зашифрованих протоколах (DoH, DoT) та надає зручний інтерфейс у стилі Glassmorphism для моніторингу мережі в реальному часі.

---

## ✨ Key Features / Ключові можливості

### 🚀 Performance & Logic / Продуктивність та логіка
- **Parallel Upstream Resolution:** Queries multiple DNS providers simultaneously (Google, Cloudflare, Quad9) and returns the fastest response.
- **Optimistic Caching:** Serves expired records from cache while updating them in the background to ensure zero-latency.
- **Conditional Routing:** Custom rules to route specific domains to specific upstream servers.

### 🔒 Security & Privacy / Безпека та приватність
- **Encrypted Protocols:** Native support for **DNS-over-HTTPS (DoH)** and **DNS-over-TLS (DoT)**.
- **Stealth Mode:** Unauthorized queries are silently dropped, making the server invisible to port scanners.
- **Robust ACL:** Advanced Access Control Lists based on IP ranges or unique Client IDs.

### 🎨 Pro-Dashboard / Адмін-панель
- **Glassmorphism UI:** Modern, responsive SPA dashboard with blur effects and dark mode support.
- **Live Query Logs:** Real-time stream of DNS requests with detailed timing and resolution data.
- **Visual Analytics:** Interactive charts showing query volume, block rates, and performance metrics.

---

## 🛠 Tech Stack / Стек технологій
- **Backend:** Python 3.12 (FastAPI, Hypercorn, DNslib)
- **Frontend:** Vanilla JS / Tailwind-inspired CSS / Chart.js
- **Container:** Docker (Alpine-based for minimal footprint)

---

## 🚀 Deployment / Розгортання

### Docker (Recommended)
```bash
docker run -d --name adb-pd \
  --network host \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v /etc/letsencrypt:/etc/letsencrypt:ro \
  --restart always \
  webyhomelab/adb-pd:latest
```

### Configuration / Налаштування
Copy `app/config.yaml.example` to `config.yaml` and adjust your settings:
```yaml
dns:
  port: 53
  upstreams:
    - https://dns.google/dns-query
    - 1.1.1.1
auth:
  password: "your_secure_password"
tls:
  enabled: true
  cert_path: "/etc/letsencrypt/live/your-domain.com/fullchain.pem"
```

---

## 📊 Monitoring / Моніторинг
The dashboard is available at `https://your-server-ip:443/` (or the port specified in config).

---

## 🤝 Contribution
Developed with ❤️ by **AddMax**. Feel free to fork and submit Pull Requests!

---

## 📜 License
MIT License. Free for personal and commercial use.
