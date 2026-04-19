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

## 🏗 System Architecture (v0.1.0-2026)

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#00d4ff', 'edgeLabelBackground':'#1a1a1a', 'tertiaryColor': '#1a1a1a'}}}%%
graph TD
    subgraph Clients ["🌐 Client Layer"]
        UserDevice["📱 Personal Devices<br/>(iOS, Android, PC)"]
        IoTDevice["🏠 Smart Home / IoT"]
        ServerNode["🖥 Remote Servers"]
    end

    subgraph EntryPoints ["🔒 Secure Access Points"]
        DNS53["📥 Standard DNS<br/>(UDP/TCP 53)"]
        DoH["🚀 DNS-over-HTTPS<br/>(JSON/Wire :443)"]
        DoT["🔐 DNS-over-TLS<br/>(Port 853)"]
        UI["🎨 Admin Dashboard<br/>(Glassmorphism SPA)"]
    end

    subgraph CoreEngine ["⚡ ADB-PD Core Processing"]
        direction TB
        AuthGate{"🛡 Security<br/>Gatekeeper"}
        
        subgraph Logic ["Processing Logic"]
            ACL["📋 ACL & CIDR<br/>Validation"]
            Filter["🚫 Adblock &<br/>Blacklist Engine"]
            Cache{"⚡ Optimistic<br/>LRU Cache"}
        end
        
        subgraph Resolution ["Upstream Handling"]
            Resolver["📡 Parallel<br/>Recursive Resolver"]
            Upstreams["Google | Cloudflare | Quad9"]
        end
    end

    subgraph Monitoring ["📊 Observability"]
        Metrics["📈 Real-time Stats"]
        Logs["📝 Live Query Stream"]
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
    
    Resolver ==>|Fastest Response| Upstreams
    Upstreams -.->|Sync Update| Cache
    
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

---

## 🤝 Contribution
Developed with ❤️ by **Weby Homelab**. Feel free to fork and submit Pull Requests!

---

## 📜 License
MIT License. Free for personal and commercial use.

<p align="center">
  Made with ❤️ in Kyiv under air raid sirens and blackouts<br>
  <strong>© 2026 Weby Homelab</strong>
</p>
