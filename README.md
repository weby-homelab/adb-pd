# 🛡️ ADB-PD (Приватний DNS Adblock)

<p align="center">
  <a href="README_ENG.md">
    <img src="https://img.shields.io/badge/🇬🇧_English-00D4FF?style=for-the-badge&logo=readme&logoColor=white" alt="English README">
  </a>
  <a href="README.md">
    <img src="https://img.shields.io/badge/🇺🇦_Українська-FF4D00?style=for-the-badge&logo=readme&logoColor=white" alt="Українська версія">
  </a>
</p>

<br>

**Високопродуктивний DNS-over-HTTPS/TLS/QUIC резолвер з професійною адмін-панеллю у стилі Glassmorphism.**

[![Docker Image Size](https://img.shields.io/docker/image-size/webyhomelab/adb-pd/latest)](https://hub.docker.com/r/webyhomelab/adb-pd)
[![Docker Pulls](https://img.shields.io/docker/pulls/webyhomelab/adb-pd)](https://hub.docker.com/r/webyhomelab/adb-pd)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌍 Огляд

**ADB-PD** — це легке, приватне DNS-рішення, створене для максимальної швидкості та повного контролю. Це сучасна альтернатива застарілим DNS-серверам, яка фокусується на зашифрованих протоколах (DoH, DoT) та надає зручний інтерфейс у стилі Glassmorphism для моніторингу мережі в реальному часі.

---

## 🏗 Архітектура системи (v0.1.0-2026)

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#00d4ff', 'edgeLabelBackground':'#1a1a1a', 'tertiaryColor': '#1a1a1a'}}}%%
graph TD
    subgraph Clients ["🌐 Рівень клієнтів"]
        UserDevice["📱 Персональні пристрої<br/>(iOS, Android, PC)"]
        IoTDevice["🏠 Розумний будинок / IoT"]
        ServerNode["🖥 Віддалені сервери"]
    end

    subgraph EntryPoints ["🔒 Точки входу"]
        DNS53["📥 Стандартний DNS<br/>(UDP/TCP 53)"]
        DoH["🚀 DNS-over-HTTPS<br/>(JSON/Wire :443)"]
        DoT["🔐 DNS-over-TLS<br/>(Порт 853)"]
        UI["🎨 Адмін-панель<br/>(Glassmorphism SPA)"]
    end

    subgraph CoreEngine ["⚡ Ядро обробки ADB-PD"]
        direction TB
        AuthGate{"🛡 Security<br/>Gatekeeper"}
        
        subgraph Logic ["Логіка обробки"]
            ACL["📋 Валідація<br/>ACL & CIDR"]
            Filter["🚫 Фільтрація<br/>Adblock & Blacklists"]
            Cache{"⚡ Оптимістичний<br/>LRU Кеш"}
        end
        
        subgraph Resolution ["Робота з апстрімами"]
            Resolver["📡 Паралельний<br/>рекурсивний резолвер"]
            Upstreams["Google | Cloudflare | Quad9"]
        end
    end

    subgraph Monitoring ["📊 Моніторинг"]
        Metrics["📈 Статистика в реальному часі"]
        Logs["📝 Потік запитів (Live)"]
    end

    %% Connections
    UserDevice & IoTDevice & ServerNode ==> DNS53 & DoH & DoT
    UI --- AuthGate
    
    DNS53 & DoH & DoT --> AuthGate
    AuthGate --> ACL
    ACL --> Filter
    Filter --> Cache
    
    Cache -- "Cache Hit" --> DNS53
    Cache -- "Cache Miss" --> Resolver
    
    Resolver ==>|Найшвидша відповідь| Upstreams
    Upstreams -.->|Синхронне оновлення| Cache
    
    Logic -.-> Metrics
    Logic -.-> Logs
    
    %% Styling
    classDef client fill:#2a2a2a,stroke:#555,stroke-width:2px,color:#fff;
    classDef secure fill:#1a3a5a,stroke:#00d4ff,stroke-width:2px,color:#fff;
    classDef core fill:#1e1e1e,stroke:#7b2ff7,stroke-width:2px,color:#fff;
    classDef monitor fill:#1a332a,stroke:#00ff88,stroke-width:2px,color:#fff;
    
    class UserDevice,IoTDevice,ServerNode client;
    class DNS53,DoH,DoT,UI secure;
    class AuthGate,ACL,Filter,Cache,Resolver,Upstreams core;
    class Metrics,Logs monitor;
```

---

## ✨ Ключові можливості

### 🚀 Продуктивність та логіка
- **Паралельне опитування апстрімів:** Опитує декілька DNS-провайдерів одночасно (Google, Cloudflare, Quad9) та повертає найшвидшу відповідь.
- **Оптимістичне кешування:** Віддає записи з кешу, термін дії яких закінчився, одночасно оновлюючи їх у фоновому режимі.
- **Умовна маршрутизація:** Спеціальні правила для перенаправлення конкретних доменів на певні DNS-сервери.

### 🔒 Безпека та приватність
- **Зашифровані протоколи:** Нативна підтримка **DNS-over-HTTPS (DoH)** та **DNS-over-TLS (DoT)**.
- **Режим Stealth:** Неавторизовані запити просто ігноруються, що робить сервер невидимим для сканерів портів.
- **Гнучкий ACL:** Просунуті списки контролю доступу на основі IP-діапазонів або Client ID.

### 🎨 Адмін-панель
- **Glassmorphism UI:** Сучасна SPA-панель з ефектами розмиття та адаптивним дизайном.
- **Live-логи:** Потік DNS-запитів у реальному часі з детальною інформацією про час обробки.
- **Візуальна аналітика:** Інтерактивні графіки обсягу запитів та ефективності фільтрації.

---

## 🛠 Стек технологій
- **Backend:** Python 3.12 (FastAPI, Hypercorn, DNslib)
- **Frontend:** Vanilla JS / Tailwind-inspired CSS / Chart.js
- **Container:** Docker (на базі Alpine)

---

## 🚀 Розгортання

### Docker (Рекомендовано)
```bash
docker run -d --name adb-pd \
  --network host \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v /etc/letsencrypt:/etc/letsencrypt:ro \
  --restart always \
  webyhomelab/adb-pd:latest
```

---

## 🤝 Співпраця
Розроблено з ❤️ командою **Weby Homelab**. Будемо раді вашим Fork та Pull Request!

---

## 📜 Ліцензія
MIT License. Вільно для особистого та комерційного використання.

<p align="center">
  Made with ❤️ in Kyiv under air raid sirens and blackouts<br>
  <strong>© 2026 Weby Homelab</strong>
</p>
