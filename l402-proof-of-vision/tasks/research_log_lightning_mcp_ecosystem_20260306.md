# Research Log — Lightning MCP Ecosystem для L402 Proof of Vision

**Date:** 2026-03-06
**Status:** DONE
**Trigger:** Выбор между DIY (ручной gRPC код) и MCP-оркестрацией (готовые инструменты)

## Контекст

После решения блокеров с LND (rpcbind, tlsextradomain, proto-файл) встал вопрос: писать L402-логику самим или использовать готовые MCP-инструменты, как мы уже делаем с астро-стеком через MCPorter.

## Исследованные инструменты

### 1. polar-mcp (jamaljsr)
- **Категория:** Оркестратор тестовых Lightning-сетей
- **Repo:** https://github.com/jamaljsr/polar-mcp
- **MCP tools:** 45 (сети, Bitcoin-операции, Lightning, Taproot Assets)
- **Поддержка:** LND, c-lightning, Eclair, litd, tapd
- **КРИТИЧЕСКИЙ БЛОКЕР:** Требует запущенный Polar GUI (Electron). HTTP bridge на `localhost:37373`. Headless/Docker НЕВОЗМОЖНО.
- **Вердикт:** Полезен как dev-tool на десктопе. Непригоден для CI/CD и headless.

### 2. refined-element/lightning-enable-mcp
- **Категория:** L402 КЛИЕНТ для AI-агентов (НЕ серверный прокси!)
- **Repo:** https://github.com/refined-element/lightning-enable-mcp
- **MCP tools:** 15 (pay_invoice, access_l402_resource, create_invoice, check_invoice_status, discover_api, budget tracking...)
- **Подключение к LND:** REST + macaroon. Также Strike, NWC, OpenNode.
- **L402 flow:** Полный клиентский — обнаружить 402 → распарсить → оплатить → повторить с preimage
- **Regtest:** ДА (парсит lnbcrt)
- **Docker:** ДА
- **ВАЖНО:** Это КЛИЕНТ, не сервер. Не создаёт L402-заставку, не слушает HTTP.
- **Вердикт:** Идеальная замена нашего client-agent. Берём для клиентской стороны.

### 3. getAlby/mcp
- **Категория:** NWC Lightning кошелёк для LLM
- **Repo:** https://github.com/getAlby/mcp
- **MCP tools:** 11 (pay_invoice, make_invoice, fetch_l402, get_balance...)
- **Подключение:** Только NWC (Nostr Wallet Connect) — не прямое gRPC к LND
- **Regtest:** Проблематично (NWC завязан на Nostr relay)
- **Вердикт:** НЕ подходит. Слишком завязан на экосистему Alby/NWC.

### 4. ehallmark/btc-lightning-client + btc-lightning-mcp-server
- **Категория:** Прямой LND gRPC клиент (Python)
- **Repo:** https://github.com/ehallmark/btc-lightning-client
- **MCP tools:** 5 (pay_invoice, create_invoice, check_invoice_is_settled, check_wallet_balance, get_public_info)
- **Подключение:** Прямое gRPC к LND (TLS + macaroon)
- **Regtest:** ДА (нативно, примеры на simnet)
- **Вердикт:** Хороший low-level fallback. Но refined-element покрывает больше.

### 5. lightninglabs/aperture ⚡ ГЛАВНАЯ НАХОДКА
- **Категория:** Production-ready L402 reverse proxy (СЕРВЕРНАЯ СТОРОНА)
- **Repo:** https://github.com/lightninglabs/aperture
- **Docker image:** `lightninglabs/aperture:v0.3-beta` (есть на Docker Hub)
- **Что делает:** Стоит перед API как reverse proxy. Полный L402 flow из коробки:
  - Запрос → 402 + macaroon + Lightning invoice
  - Клиент платит → получает preimage
  - Повторный запрос с preimage → Aperture верифицирует → проксирует к backend
- **Подключение к LND:** gRPC (host + tls.cert + macaroon dir)
- **Regtest:** ДА (`authenticator.network: "regtest"`)
- **Конфиг:** YAML, сервисы с hostregexp/pathregexp, price в sats, rate limits
- **Production use:** Lightning Loop (Lightning Labs)
- **Вердикт:** Это ровно то, что нам нужно для серверной стороны. Заменяет ВСЮ L402-логику в mock-api.

### 6. Другие (не подходят)
- **PayGated:** Кредитная система + Stripe. Не L402, не Lightning.
- **SatGate MCP Proxy:** Бюджетный прокси на клиенте. Не создаёт инвойсы.
- **lightningfaucet/lightning-wallet-mcp:** SaaS (40+ tools), нет regtest, нет self-host.

## Итоговая матрица

| Задача | Инструмент | Статус |
|---|---|---|
| Серверная L402-заставка | **Aperture** (Lightning Labs) | Берём |
| Клиент-агент (оплата L402) | **refined-element/lightning-enable-mcp** | Берём |
| Тестовая инфраструктура | Docker Compose (bitcoind + 2x LND) | Руками |
| Dev-тестирование | polar-mcp (опционально, с Polar GUI) | Опционально |

## Целевая архитектура

```
client-agent ──→ Aperture (:8081) ──→ astro-api (:3000)
  (refined-element MCP)  (L402 gate)     (чистый backend)
       ↕                      ↕
    lnd-client              lnd (server)
       ↕                      ↕
            bitcoind (regtest)
```

- **mock-api** становится чистым backend (просто отдаёт данные, без L402)
- **Aperture** делает всю L402-магию (invoice, macaroon, verify)
- **refined-element** на стороне клиента автоматически платит

## Self-Check

### Что было неверно в первоначальном анализе?
1. refined-element описан как "L402-прокси" — на самом деле это КЛИЕНТ, не сервер. Исправлено после deep dive в исходники.

### Как не делать
1. Не писать L402-логику самим — Aperture уже production-ready и используется в Lightning Loop.
2. Не привязываться к NWC/Alby экосистеме — не работает с regtest без дополнительной инфраструктуры.
3. Не путать клиентскую и серверную стороны L402.

### Как делать правильно
1. Серверная сторона = Aperture (reverse proxy, YAML-конфиг, Docker image).
2. Клиентская сторона = refined-element или ehallmark (прямое подключение к LND).
3. Инфраструктура = Docker Compose с двумя LND + bitcoind в regtest.

## Sources
- https://github.com/lightninglabs/aperture
- https://github.com/lightninglabs/aperture/blob/master/sample-conf.yaml
- https://docs.lightning.engineering/the-lightning-network/l402
- https://docs.lightning.engineering/lightning-network-tools/aperture
- https://github.com/refined-element/lightning-enable-mcp
- https://github.com/getAlby/mcp
- https://github.com/ehallmark/btc-lightning-client
- https://github.com/jamaljsr/polar-mcp
