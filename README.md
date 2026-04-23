# 🛑 PROJECT ARCHIVED / ПРОЄКТ ЗАКРИТО
**[UKR] Цей проєкт офіційно закрито та архівовано (04.2026). Розробка перенесена у приватний стек нових систем безпеки.**
**[ENG] This project is officially closed and archived (04.2026). Development moved to a private stack of next-gen security systems.**

---

# 🛡️ ADB-PD (Private DNS Adblock) / Приватний DNS Adblock

**High-performance DNS-over-HTTPS/TLS/QUIC resolver with a pro-grade Glassmorphism Dashboard.**
**Високопродуктивний DNS-over-HTTPS/TLS/QUIC резолвер з професійною адмін-панеллю у стилі Glassmorphism.**

[![Docker Image Size](https://img.shields.io/docker/image-size/webyhomelab/adb-pd/latest)](https://hub.docker.com/r/webyhomelab/adb-pd)
[![Docker Pulls](https://img.shields.io/docker/pulls/webyhomelab/adb-pd)](https://hub.docker.com/r/webyhomelab/adb-pd)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌍 Overview / Огляд

**ADB-PD** is a "heavily hardened", lightweight, self-hosted DNS solution designed for absolute privacy, speed, and total control. It is a modern alternative to legacy DNS servers, focusing on encrypted protocols (DoH, DoT) and providing a "Zero Telemetry" environment. Developed in Kyiv, it transforms your DNS into a "black box" that stays strictly within your local environment.

**ADB-PD** — це "максимально захищене", легке, приватне DNS-рішення, створене для абсолютної приватності, швидкості та повного контролю. Це сучасна альтернатива застарілим DNS-серверам, яка фокусується на зашифрованих протоколах (DoH, DoT) та забезпечує середовище з "нульовою телеметрією". Розроблений у Києві, цей проект перетворює ваш DNS на "чорну скриньку", яка працює виключно у вашому локальному середовищі.

---

## ✨ Key Features / Ключові можливості

### 🚀 Performance & Logic / Продуктивність та логіка
- **Parallel Upstream Resolution:** Queries multiple DNS providers simultaneously (Google, Cloudflare, Quad9) and returns the fastest response.
- **Optimistic Caching:** Serves expired records from cache while updating them in the background.
- **Conditional Routing:** Custom rules to route specific domains to specific upstream servers.
- **Паралельне опитування апстрімів:** Опитує декілька DNS-провайдерів одночасно (Google, Cloudflare, Quad9) та повертає найшвидшу відповідь.
- **Оптимістичне кешування:** Віддає записи з кешу, термін дії яких закінчився, одночасно оновлюючи їх у фоновому режимі.
- **Умовна маршрутизація:** Спеціальні правила для перенаправлення конкретних доменів на певні DNS-сервери.

### 🔒 Security & Privacy / Безпека та приватність
- **Zero Telemetry:** Physically purged updater and telemetry modules. No "phone-home" logic.
- **Encrypted Protocols:** Native support for **DNS-over-HTTPS (DoH)** and **DNS-over-TLS (DoT)**.
- **Stealth Mode:** Unauthorized queries are silently dropped, making the server invisible to port scanners.
- **Нульова телеметрія:** Повністю видалені модулі оновлення та аналітики. Жодної логіки "дзвінків додому".
- **Зашифровані протоколи:** Нативна підтримка **DNS-over-HTTPS (DoH)** та **DNS-over-TLS (DoT)**.
- **Режим Stealth:** Неавторизовані запити просто ігноруються, що робить сервер невидимим для сканерів портів.

### 🎨 Pro-Dashboard / Адмін-панель
- **Glassmorphism UI:** Modern, responsive SPA dashboard with blur effects and visual analytics.
- **Live Query Logs:** Real-time stream of DNS requests with detailed timing and rule matching.
- **Glassmorphism UI:** Сучасна SPA-панель з ефектами розмиття, адаптивним дизайном та візуальною аналітикою.
- **Live-логи:** Потік DNS-запитів у реальному часі з детальною інформацією про час обробки та спрацьовані правила.

---

## 🛠 Tech Stack / Стек технологій
- **Backend:** Python 3.12 (FastAPI, Hypercorn, DNslib)
- **Frontend:** Vanilla JS / Tailwind-inspired CSS / Chart.js
- **Container:** Docker (Debian-Slim-based, non-root execution)

---

## 🚀 Deployment / Розгортання

### Docker (Recommended / Рекомендовано)
```bash
docker run -d --name adb-pd \
  --network host \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v /etc/letsencrypt:/etc/letsencrypt:ro \
  --restart always \
  webyhomelab/adb-pd:latest
```

---

## 🤝 Contribution / Співпраця
Developed with ❤️ by **Weby Homelab**. Feel free to fork and submit Pull Requests!
Розроблено з ❤️ командою **Weby Homelab**. Будемо раді вашим Fork та Pull Request!

---

## 📜 License / Ліцензія
MIT License. Free for personal and commercial use.
MIT License. Вільно для особистого та комерційного використання.

<p align="center">
  Made with ❤️ in Kyiv under air raid sirens and blackouts<br>
  <strong>© 2026 Weby Homelab</strong>
</p>
