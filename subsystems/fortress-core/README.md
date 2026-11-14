# Faery Fortress — Sovereign Substrate (BSL 1.1)

The autonomous revenue infrastructure behind RasaXM Alpha: API bridge, RGU
portfolio ledger, cross-venue arb worker, market feed, Telegram herald, social
outreach drafts, in-house CRM, demand-gen harvester, email ops, JobMatch PWA
backend, GDPR vault interface, financial projections engine.

Live: [`fortress.rasaxmachina.com`](https://fortress.rasaxmachina.com) ·
Signals: [`alpha`](https://alpha.rasaxmachina.com) · Track record:
[`ledger`](https://ledger.rasaxmachina.com)

## License — read this first

**BSL 1.1**: free to read, learn, fork, self-host NON-commercially. Production
(commercial, revenue, customer-facing) use needs a commercial license
($999 Sovereign Substrate tier) → [Gumroad](https://coltak.gumroad.com).
Converts to Apache-2.0 automatically on 2030-09-05.

## Run it (paper mode, $0)

```bash
python tx_market_feed.py once        # market snapshot, no keys
python tx_arb_worker.py once        # paper arb cycle (DRY-RUN default)
python tx_leadgen.py harvest        # HN/Reddit/GitHub demand-gen -> CRM
python tx_crm.py list               # pipeline view
python tx_gui_bridge.py             # API substrate (health, checkout, SSE)
```

Real-money rails (Stripe, exchanges) stay DRY-RUN until YOU fund accounts.
The substrate never holds money — design principle, not a limitation.

## Modules

| File | Role |
|---|---|
| `tx_gui_bridge.py` | API substrate: health, checkout, webhooks, SSE, jobmatch |
| `tx_arb_worker.py` | cross-venue arb loop (paper until funded) |
| `tx_market_feed.py` | spot/funding-rate market scanner |
| `tx_telegram_herald.py` | autonomous signal publisher (15-min loop) |
| `tx_social_herald.py` | X/Reddit/HN/LinkedIn drafts, honesty firewall |
| `tx_crm.py` + `tx_leadgen.py` | SQLite CRM + ICP-scored demand harvester |
| `tx_email_ops.py` | Resend digest + lead flows |
| `tx_jobmatch.py` | 50%-coverage-gate resume engine |
| `tx_gdpr_vault.py` | Articles 15–35 data-subject rights |
| `tx_projections_v2.py` | 4-posture compounding model (intent, not fact) |

## Proof, not promises
Ledger: $44.50 realized, every event hash-logged. Paper fills labeled paper.
Sister MIT repos: [007-scanner](https://github.com/Tianxia-Core/AegisScan) ·
[secrets-vault](https://github.com/Tianxia-Core/AetherVault)
