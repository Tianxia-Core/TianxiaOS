#!/usr/bin/env python3
# ffp: FFP-I18N-ENGINE content-pipeline python
"""
TianxiaOS / Rasa-X-Machina — Sovereign 42-Market, 29-Currency & 25-Language Compiler
====================================================================================
DSS-14.2 & SLECO-SO++ compliant localization and multi-fiat market compiler.

Responsibilities:
1. Compile `tianxia/ui/pricing.json` with 29 fiat currencies (anchored to EUR=1.0,
   decimal precision 0 for JPY/KRW/VND/CLP and 2 for all others) and 42 sovereign
   country/regional markets.
2. Extract 100% of static HTML text nodes, translatable attributes, post-money-split
   text fragments, dynamic modal/dock/console templates, and catalog strings across
   all 33 HTML portals, `tx_web_standards.js`, `subdomains.json`, and `pricing.json`.
3. Decompose repeated structural wrappers (emoji/SKU badges, directional arrows,
   punctuation frames) and protect invariant technical/legal tokens (`TianxiaOS`,
   `RASA-X-MACHINA OÜ`, `Dealum`, `#179423`, `§ 100¹`, `seL4`, `NixOS`, `Rosenpass`,
   `WireGuard`, `TetraLedger`, `GDPR++`, SKU IDs, URLs, cryptographic addresses)
   to maximize localization reuse and fidelity.
4. Generate `/tianxia/ui/i18n/<lang>.json` for all 25 languages (`en` + 24 translated
   packs including RTL `ar` and `ur`) and `/tianxia/ui/i18n/index.json`, then
   programmatically verify 100% string coverage across all 33 HTML files.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import glob
import http.client
import json
import logging
import math
import os
import re
import ssl
import threading
import time
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="[tx_i18n_engine] %(levelname)s %(message)s",
)
LOG = logging.getLogger("tx_i18n_engine")

REPO_DIR = Path(__file__).resolve().parent.parent
UI_DIR = Path(os.environ.get("TX_UI_DIR", str(REPO_DIR / "ui")))
I18N_DIR = UI_DIR / "i18n"
PRICING_PATH = UI_DIR / "pricing.json"
SUBDOMAINS_CFG_PATH = REPO_DIR / "config" / "subdomains.json"

# ---------------------------------------------------------------------------
# 1. CANONICAL 29 CURRENCIES (Anchored to EUR = 1.0)
# ---------------------------------------------------------------------------
CURRENCIES_29: Dict[str, dict] = {
    "EUR": {"code": "EUR", "symbol": "€", "name": "Euro", "rate": 1.0, "decimals": 2, "zero_decimal": False, "countries": ["EE", "DE", "FR", "FI", "LT", "BE", "NL", "IT", "ES", "CY", "GR", "MT", "EU"]},
    "USD": {"code": "USD", "symbol": "$", "name": "US Dollar", "rate": 1.08, "decimals": 2, "zero_decimal": False, "countries": ["US", "GLOBAL"]},
    "GBP": {"code": "GBP", "symbol": "£", "name": "British Pound", "rate": 0.85, "decimals": 2, "zero_decimal": False, "countries": ["GB"]},
    "CHF": {"code": "CHF", "symbol": "CHF ", "name": "Swiss Franc", "rate": 0.95, "decimals": 2, "zero_decimal": False, "countries": ["CH"]},
    "SEK": {"code": "SEK", "symbol": "kr ", "name": "Swedish Krona", "rate": 11.45, "decimals": 2, "zero_decimal": False, "countries": ["SE"]},
    "NOK": {"code": "NOK", "symbol": "kr ", "name": "Norwegian Krone", "rate": 11.70, "decimals": 2, "zero_decimal": False, "countries": ["NO"]},
    "SGD": {"code": "SGD", "symbol": "S$", "name": "Singapore Dollar", "rate": 1.45, "decimals": 2, "zero_decimal": False, "countries": ["SG"]},
    "JPY": {"code": "JPY", "symbol": "¥", "name": "Japanese Yen", "rate": 164.0, "decimals": 0, "zero_decimal": True, "countries": ["JP"]},
    "HKD": {"code": "HKD", "symbol": "HK$", "name": "Hong Kong Dollar", "rate": 8.40, "decimals": 2, "zero_decimal": False, "countries": ["HK"]},
    "CAD": {"code": "CAD", "symbol": "CA$", "name": "Canadian Dollar", "rate": 1.50, "decimals": 2, "zero_decimal": False, "countries": ["CA"]},
    "VND": {"code": "VND", "symbol": "₫", "name": "Vietnamese Dong", "rate": 27500.0, "decimals": 0, "zero_decimal": True, "countries": ["VN"]},
    "KRW": {"code": "KRW", "symbol": "₩", "name": "South Korean Won", "rate": 1490.0, "decimals": 0, "zero_decimal": True, "countries": ["KR"]},
    "NGN": {"code": "NGN", "symbol": "₦", "name": "Nigerian Naira", "rate": 1750.0, "decimals": 2, "zero_decimal": False, "countries": ["NG"]},
    "KES": {"code": "KES", "symbol": "KSh ", "name": "Kenyan Shilling", "rate": 140.0, "decimals": 2, "zero_decimal": False, "countries": ["KE"]},
    "BRL": {"code": "BRL", "symbol": "R$", "name": "Brazilian Real", "rate": 6.15, "decimals": 2, "zero_decimal": False, "countries": ["BR"]},
    "MXN": {"code": "MXN", "symbol": "MX$", "name": "Mexican Peso", "rate": 21.60, "decimals": 2, "zero_decimal": False, "countries": ["MX"]},
    "CLP": {"code": "CLP", "symbol": "CLP$", "name": "Chilean Peso", "rate": 1035.0, "decimals": 0, "zero_decimal": True, "countries": ["CL"]},
    "ARS": {"code": "ARS", "symbol": "AR$", "name": "Argentine Peso", "rate": 1090.0, "decimals": 2, "zero_decimal": False, "countries": ["AR"]},
    "COP": {"code": "COP", "symbol": "COL$", "name": "Colombian Peso", "rate": 4680.0, "decimals": 2, "zero_decimal": False, "countries": ["CO"]},
    "INR": {"code": "INR", "symbol": "₹", "name": "Indian Rupee", "rate": 91.50, "decimals": 2, "zero_decimal": False, "countries": ["IN"]},
    "PKR": {"code": "PKR", "symbol": "Rs ", "name": "Pakistani Rupee", "rate": 301.0, "decimals": 2, "zero_decimal": False, "countries": ["PK"]},
    "PLN": {"code": "PLN", "symbol": "zł ", "name": "Polish Zloty", "rate": 4.32, "decimals": 2, "zero_decimal": False, "countries": ["PL"]},
    "BGN": {"code": "BGN", "symbol": "лв ", "name": "Bulgarian Lev", "rate": 1.9558, "decimals": 2, "zero_decimal": False, "countries": ["BG"]},
    "TRY": {"code": "TRY", "symbol": "₺", "name": "Turkish Lira", "rate": 37.80, "decimals": 2, "zero_decimal": False, "countries": ["TR"]},
    "AUD": {"code": "AUD", "symbol": "A$", "name": "Australian Dollar", "rate": 1.65, "decimals": 2, "zero_decimal": False, "countries": ["AU"]},
    "NZD": {"code": "NZD", "symbol": "NZ$", "name": "New Zealand Dollar", "rate": 1.81, "decimals": 2, "zero_decimal": False, "countries": ["NZ"]},
    "ZAR": {"code": "ZAR", "symbol": "R ", "name": "South African Rand", "rate": 19.40, "decimals": 2, "zero_decimal": False, "countries": ["ZA"]},
    "AED": {"code": "AED", "symbol": "AED ", "name": "UAE Dirham", "rate": 3.97, "decimals": 2, "zero_decimal": False, "countries": ["AE"]},
    "SAR": {"code": "SAR", "symbol": "SAR ", "name": "Saudi Riyal", "rate": 4.05, "decimals": 2, "zero_decimal": False, "countries": ["SA"]},
}

for _cc, _cmeta in CURRENCIES_29.items():
    _cmeta["rate_from_eur"] = _cmeta["rate"]
    _cmeta["rate_from_usd"] = round(_cmeta["rate"] / 1.08, 6)

# ---------------------------------------------------------------------------
# 2. CANONICAL 25 LANGUAGES (Reused Across All 42 Markets)
# ---------------------------------------------------------------------------
LANGUAGES_25: Dict[str, dict] = {
    "en": {"lang": "en", "gtx": "en", "dir": "ltr", "name": "English", "native_name": "English", "markets": ["EE", "GB", "US", "CA", "AU", "NZ", "SG", "HK", "NG", "KE", "ZA", "IN", "PK", "MT", "CY", "AE", "SA", "EU", "GLOBAL"]},
    "et": {"lang": "et", "gtx": "et", "dir": "ltr", "name": "Estonian", "native_name": "Eesti", "markets": ["EE", "EU"]},
    "de": {"lang": "de", "gtx": "de", "dir": "ltr", "name": "German", "native_name": "Deutsch", "markets": ["DE", "CH", "BE", "EU"]},
    "fr": {"lang": "fr", "gtx": "fr", "dir": "ltr", "name": "French", "native_name": "Français", "markets": ["FR", "CA", "BE", "CH", "EU"]},
    "es": {"lang": "es", "gtx": "es", "dir": "ltr", "name": "Spanish", "native_name": "Español", "markets": ["ES", "MX", "CL", "AR", "CO", "US", "EU"]},
    "pt": {"lang": "pt", "gtx": "pt", "dir": "ltr", "name": "Portuguese", "native_name": "Português", "markets": ["BR", "EU"]},
    "it": {"lang": "it", "gtx": "it", "dir": "ltr", "name": "Italian", "native_name": "Italiano", "markets": ["IT", "CH", "EU"]},
    "nl": {"lang": "nl", "gtx": "nl", "dir": "ltr", "name": "Dutch", "native_name": "Nederlands", "markets": ["NL", "BE", "EU"]},
    "pl": {"lang": "pl", "gtx": "pl", "dir": "ltr", "name": "Polish", "native_name": "Polski", "markets": ["PL", "EU"]},
    "fi": {"lang": "fi", "gtx": "fi", "dir": "ltr", "name": "Finnish", "native_name": "Suomi", "markets": ["FI", "EU"]},
    "lt": {"lang": "lt", "gtx": "lt", "dir": "ltr", "name": "Lithuanian", "native_name": "Lietuvių", "markets": ["LT", "EU"]},
    "bg": {"lang": "bg", "gtx": "bg", "dir": "ltr", "name": "Bulgarian", "native_name": "Български", "markets": ["BG", "EU"]},
    "el": {"lang": "el", "gtx": "el", "dir": "ltr", "name": "Greek", "native_name": "Ελληνικά", "markets": ["GR", "CY", "EU"]},
    "mt": {"lang": "mt", "gtx": "mt", "dir": "ltr", "name": "Maltese", "native_name": "Malti", "markets": ["MT", "EU"]},
    "sv": {"lang": "sv", "gtx": "sv", "dir": "ltr", "name": "Swedish", "native_name": "Svenska", "markets": ["SE", "FI", "EU"]},
    "no": {"lang": "no", "gtx": "no", "dir": "ltr", "name": "Norwegian", "native_name": "Norsk", "markets": ["NO"]},
    "tr": {"lang": "tr", "gtx": "tr", "dir": "ltr", "name": "Turkish", "native_name": "Türkçe", "markets": ["TR", "CY"]},
    "ar": {"lang": "ar", "gtx": "ar", "dir": "rtl", "name": "Arabic", "native_name": "العربية", "markets": ["AE", "SA"]},
    "ur": {"lang": "ur", "gtx": "ur", "dir": "rtl", "name": "Urdu", "native_name": "اردو", "markets": ["PK"]},
    "hi": {"lang": "hi", "gtx": "hi", "dir": "ltr", "name": "Hindi", "native_name": "हिन्दी", "markets": ["IN"]},
    "sw": {"lang": "sw", "gtx": "sw", "dir": "ltr", "name": "Swahili", "native_name": "Kiswahili", "markets": ["KE"]},
    "vi": {"lang": "vi", "gtx": "vi", "dir": "ltr", "name": "Vietnamese", "native_name": "Tiếng Việt", "markets": ["VN"]},
    "ko": {"lang": "ko", "gtx": "ko", "dir": "ltr", "name": "Korean", "native_name": "한국어", "markets": ["KR"]},
    "zh-HK": {"lang": "zh-HK", "gtx": "zh-TW", "dir": "ltr", "name": "Traditional Chinese (HK)", "native_name": "繁體中文 (香港)", "markets": ["HK", "SG"]},
    "ja": {"lang": "ja", "gtx": "ja", "dir": "ltr", "name": "Japanese", "native_name": "日本語", "markets": ["JP"]},
}

# ---------------------------------------------------------------------------
# 3. CANONICAL 42 MARKETS (12 Existing + 30 Newly Expanded Countries/Regions)
# ---------------------------------------------------------------------------
MARKETS_42: Dict[str, dict] = {
    # Existing 12 Markets
    "EE": {"code": "EE", "flag": "🇪🇪", "name": "Estonia", "native_name": "Eesti", "currency": "EUR", "default_lang": "et", "languages": ["et", "en"], "regime": "Estonian Aliens Act § 100¹ (Dealum #179423 Under Committee Review) · AKI / IKS · EU AI Act · GDPR++ v2030.4", "rails": "Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · Paddle · x402", "edge": "Hetzner EU Rosenpass PQ Relay (<TX_RELAY_IPV4> · ~12ms Baltic RTT)"},
    "DE": {"code": "DE", "flag": "🇩🇪", "name": "Germany", "native_name": "Deutschland", "currency": "EUR", "default_lang": "de", "languages": ["de", "en"], "regime": "BSI IT-Grundschutz · DSGVO++ · NIS2 & DORA Sovereign Enclave · GDPR++ v2030.4", "rails": "Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · Paddle MoR", "edge": "Hetzner EU Rosenpass PQ Relay (<TX_RELAY_IPV4> · <9ms DE RTT)"},
    "FR": {"code": "FR", "flag": "🇫🇷", "name": "France", "native_name": "France", "currency": "EUR", "default_lang": "fr", "languages": ["fr", "en"], "regime": "CNIL RGPD++ · ANSSI SecNumCloud Principles · NIS2 & EU AI Act · GDPR++ v2030.4", "rails": "Stripe EUR (€) Cartes Bancaires / SEPA · Solana Pay · Base L2 · Paddle", "edge": "European Rosenpass PQ Relay (~17ms Paris RTT)"},
    "GB": {"code": "GB", "flag": "🇬🇧", "name": "United Kingdom", "native_name": "United Kingdom", "currency": "GBP", "default_lang": "en", "languages": ["en"], "regime": "UK GDPR / DUAA · NCSC Zero-Trust Enclave Alignment · GDPR++ v2030.4", "rails": "Stripe GBP (£) Cards / Faster Payments · Solana Pay · Base L2 · Paddle", "edge": "European Rosenpass PQ Relay (~21ms London RTT)"},
    "US": {"code": "US", "flag": "🇺🇸", "name": "United States", "native_name": "United States", "currency": "USD", "default_lang": "en", "languages": ["en", "es"], "regime": "CCPA / CPRA · NIST FIPS 203 Post-Quantum · Sec-GPC: 1 Auto-Honored · GDPR++ v2030.4", "rails": "Stripe USD ($) Cards / Link · Base L2 USDC · Solana Pay · Gumroad · x402", "edge": "Global Anycast TLS 1.3 + Sovereign PQ Tunnel"},
    "CH": {"code": "CH", "flag": "🇨🇭", "name": "Switzerland", "native_name": "Schweiz / Suisse / Svizzera", "currency": "CHF", "default_lang": "de", "languages": ["de", "fr", "it", "en"], "regime": "Swiss revFADP (nDSG) · FINMA Zero-Knowledge Enclave Standard · GDPR++ v2030.4", "rails": "Native Stripe CHF · Solana Pay · Base L2 USDC · x402", "edge": "European Rosenpass PQ Relay (~15ms Zurich RTT)"},
    "SE": {"code": "SE", "flag": "🇸🇪", "name": "Sweden", "native_name": "Sverige", "currency": "SEK", "default_lang": "sv", "languages": ["sv", "en"], "regime": "IMY Dataskydd++ · NIS2 & Nordic Sovereign Infrastructure · GDPR++ v2030.4", "rails": "Native Stripe SEK (kr) · Solana Pay · Base L2 · Paddle MoR", "edge": "Baltic/Nordic Rosenpass PQ Relay (~11ms Stockholm RTT)"},
    "NO": {"code": "NO", "flag": "🇳🇴", "name": "Norway", "native_name": "Norge", "currency": "NOK", "default_lang": "no", "languages": ["no", "en"], "regime": "Datatilsynet Personvern++ · NSM Zero-Trust & NIS2 · GDPR++ v2030.4", "rails": "Native Stripe NOK (kr) · Solana Pay · Base L2 · Paddle MoR", "edge": "Nordic Rosenpass PQ Relay (~15ms Oslo RTT)"},
    "SG": {"code": "SG", "flag": "🇸🇬", "name": "Singapore", "native_name": "Singapore / 新加坡", "currency": "SGD", "default_lang": "en", "languages": ["en", "zh-HK"], "regime": "Singapore PDPA & MAS TRM Cyber-Resilience · GDPR++ v2030.4", "rails": "Native Stripe SGD (S$) · Solana Pay · Base L2 USDC · Agentic x402", "edge": "APAC Sovereign Edge + Post-Quantum Mesh"},
    "JP": {"code": "JP", "flag": "🇯🇵", "name": "Japan", "native_name": "日本", "currency": "JPY", "default_lang": "ja", "languages": ["ja", "en"], "regime": "APPI (個人情報保護法) · Post-Quantum Cryptoshredding (<50ms) · GDPR++ v2030.4", "rails": "Native Stripe JPY (¥) · Solana Pay · Base L2 · x402", "edge": "APAC TLS 1.3 Edge + Post-Quantum Rosenpass Relay"},
    "EU": {"code": "EU", "flag": "🇪🇺", "name": "European Union", "native_name": "European Union", "currency": "EUR", "default_lang": "en", "languages": ["en", "de", "fr", "es", "it", "nl", "pl", "et", "fi", "lt", "bg", "el", "mt", "sv", "pt"], "regime": "EU GDPR (2016/679) · EU AI Act · NIS2 & DORA · GDPR++ v2030.4", "rails": "Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · Paddle MoR · x402", "edge": "Hetzner European Post-Quantum Rosenpass Mesh"},
    "GLOBAL": {"code": "GLOBAL", "flag": "🌐", "name": "Global (International)", "native_name": "Global", "currency": "USD", "default_lang": "en", "languages": ["en", "es", "fr", "ar", "zh-HK", "ja"], "regime": "ISO/IEC 27701 · NIST FIPS 203 ML-KEM-1024 · GDPR++ Sovereign Horizon v2030.4", "rails": "Stripe Multi-Currency · Solana Pay · Base L2 · Gumroad · Paddle · x402", "edge": "Global Anycast TLS 1.3 + Post-Quantum WireGuard Mesh"},
    # 30 Newly Expanded Countries & Territories
    "HK": {"code": "HK", "flag": "🇭🇰", "name": "Hong Kong", "native_name": "香港", "currency": "HKD", "default_lang": "zh-HK", "languages": ["zh-HK", "en"], "regime": "Hong Kong PDPO (Cap. 486) · HKMA Cyber Resilience · GDPR++ v2030.4", "rails": "Stripe HKD (HK$) Cards / FPS · Solana Pay · Base L2 USDC · x402", "edge": "APAC East Edge + Post-Quantum Rosenpass Tunnel"},
    "CA": {"code": "CA", "flag": "🇨🇦", "name": "Canada", "native_name": "Canada", "currency": "CAD", "default_lang": "en", "languages": ["en", "fr"], "regime": "PIPEDA & Québec Law 25 · Post-Quantum Cryptoshredding · GDPR++ v2030.4", "rails": "Native Stripe CAD (CA$) · Base L2 USDC · Solana Pay · Paddle", "edge": "North American TLS 1.3 Edge + PQ Sovereign Relay"},
    "VN": {"code": "VN", "flag": "🇻🇳", "name": "Vietnam", "native_name": "Việt Nam", "currency": "VND", "default_lang": "vi", "languages": ["vi", "en"], "regime": "Vietnam PDPD (Decree 13/2023/ND-CP) · Sovereign Enclave Isolation · GDPR++ v2030.4", "rails": "Stripe VND (₫) Cards · Solana Pay · Base L2 USDC · Paddle · x402", "edge": "SEA Edge Ingress + Post-Quantum WireGuard Relay"},
    "KR": {"code": "KR", "flag": "🇰🇷", "name": "South Korea", "native_name": "대한민국", "currency": "KRW", "default_lang": "ko", "languages": ["ko", "en"], "regime": "South Korea PIPA (개인정보 보호법) · ISMS-P Enclave Standard · GDPR++ v2030.4", "rails": "Stripe KRW (₩) Cards · Solana Pay · Base L2 USDC · Paddle · x402", "edge": "Northeast Asia TLS 1.3 Edge + Post-Quantum Mesh"},
    "NG": {"code": "NG", "flag": "🇳🇬", "name": "Nigeria", "native_name": "Nigeria", "currency": "NGN", "default_lang": "en", "languages": ["en"], "regime": "Nigeria Data Protection Act (NDPA 2023) · Zero-Trust Cryptoshredding · GDPR++ v2030.4", "rails": "Stripe NGN (₦) International Cards · Solana Pay · Base L2 USDC · x402", "edge": "West Africa Anycast Edge + EU Rosenpass PQ Relay"},
    "KE": {"code": "KE", "flag": "🇰🇪", "name": "Kenya", "native_name": "Kenya", "currency": "KES", "default_lang": "sw", "languages": ["sw", "en"], "regime": "Kenya Data Protection Act (ODPC) · Zero-Knowledge Audit · GDPR++ v2030.4", "rails": "Stripe KES (KSh) Cards · Solana Pay · Base L2 USDC · Paddle · x402", "edge": "East Africa Anycast Edge + EU Rosenpass PQ Relay"},
    "BR": {"code": "BR", "flag": "🇧🇷", "name": "Brazil", "native_name": "Brasil", "currency": "BRL", "default_lang": "pt", "languages": ["pt", "en"], "regime": "Brazil LGPD (Lei 13.709) · ANPD Post-Quantum Sovereignty · GDPR++ v2030.4", "rails": "Stripe BRL (R$) Cards · Solana Pay · Base L2 USDC · Paddle MoR · x402", "edge": "South America TLS 1.3 Edge + Post-Quantum Mesh"},
    "MX": {"code": "MX", "flag": "🇲🇽", "name": "Mexico", "native_name": "México", "currency": "MXN", "default_lang": "es", "languages": ["es", "en"], "regime": "Mexico LFPDPPP (INAI) · Zero-Knowledge Enclave Protection · GDPR++ v2030.4", "rails": "Stripe MXN (MX$) Cards · Solana Pay · Base L2 USDC · Paddle · x402", "edge": "LATAM North TLS 1.3 Edge + PQ Sovereign Tunnel"},
    "CL": {"code": "CL", "flag": "🇨🇱", "name": "Chile", "native_name": "Chile", "currency": "CLP", "default_lang": "es", "languages": ["es", "en"], "regime": "Chile Data Protection Law 21.719 · Cybersecurity Framework 21.663 · GDPR++ v2030.4", "rails": "Stripe CLP (CLP$) Cards · Solana Pay · Base L2 USDC · Paddle · x402", "edge": "Southern Cone TLS 1.3 Edge + PQ Sovereign Relay"},
    "AR": {"code": "AR", "flag": "🇦🇷", "name": "Argentina", "native_name": "Argentina", "currency": "ARS", "default_lang": "es", "languages": ["es", "en"], "regime": "Argentina LPDP (Ley 25.326 · AAIP) · Cryptographic Solvency · GDPR++ v2030.4", "rails": "Stripe ARS (AR$) · Solana Pay ($SOL/USDC) · Base L2 USDC · x402", "edge": "Southern Cone TLS 1.3 Edge + Post-Quantum Mesh"},
    "CO": {"code": "CO", "flag": "🇨🇴", "name": "Colombia", "native_name": "Colombia", "currency": "COP", "default_lang": "es", "languages": ["es", "en"], "regime": "Colombia Ley 1581 (SIC Habeas Data) · Enclave Isolation · GDPR++ v2030.4", "rails": "Stripe COP (COL$) Cards · Solana Pay · Base L2 USDC · Paddle · x402", "edge": "Andean TLS 1.3 Edge + Post-Quantum WireGuard Mesh"},
    "IN": {"code": "IN", "flag": "🇮🇳", "name": "India", "native_name": "भारत", "currency": "INR", "default_lang": "hi", "languages": ["hi", "en"], "regime": "India DPDP Act 2023 · CERT-In Enclave Telemetry · GDPR++ v2030.4", "rails": "Stripe INR (₹) Cards · Solana Pay · Base L2 USDC · Paddle MoR · x402", "edge": "South Asia Anycast Edge + Post-Quantum Rosenpass Mesh"},
    "PK": {"code": "PK", "flag": "🇵🇰", "name": "Pakistan", "native_name": "پاکستان", "currency": "PKR", "default_lang": "ur", "languages": ["ur", "en"], "regime": "Pakistan PDPA Framework & Zero-Trust Enclave Hardening · GDPR++ v2030.4", "rails": "Stripe PKR (Rs) Cards · Solana Pay · Base L2 USDC · Gumroad · x402", "edge": "South Asia TLS 1.3 Edge + EU Post-Quantum Relay"},
    "PL": {"code": "PL", "flag": "🇵🇱", "name": "Poland", "native_name": "Polska", "currency": "PLN", "default_lang": "pl", "languages": ["pl", "en"], "regime": "UODO RODO++ · NIS2 & EU AI Act Enclave Compliance · GDPR++ v2030.4", "rails": "Stripe PLN (zł) Cards / BLIK · Solana Pay · Base L2 · Paddle MoR", "edge": "Central Europe Rosenpass PQ Relay (~11ms Warsaw RTT)"},
    "FI": {"code": "FI", "flag": "🇫🇮", "name": "Finland", "native_name": "Suomi", "currency": "EUR", "default_lang": "fi", "languages": ["fi", "sv", "en"], "regime": "Tietosuojavaltuutettu · Traficom Kyberturvallisuus & NIS2 · GDPR++ v2030.4", "rails": "Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · Paddle MoR", "edge": "Baltic/Nordic Rosenpass PQ Relay (~9ms Helsinki RTT)"},
    "LT": {"code": "LT", "flag": "🇱🇹", "name": "Lithuania", "native_name": "Lietuva", "currency": "EUR", "default_lang": "lt", "languages": ["lt", "en"], "regime": "VDAI BDAR++ · NKSC Cyber-Resilience & NIS2 · GDPR++ v2030.4", "rails": "Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · Paddle MoR", "edge": "Baltic Rosenpass PQ Relay (~13ms Vilnius RTT)"},
    "BG": {"code": "BG", "flag": "🇧🇬", "name": "Bulgaria", "native_name": "България", "currency": "BGN", "default_lang": "bg", "languages": ["bg", "en"], "regime": "CPDP (КЗЛД) GDPR++ · NIS2 & EU AI Act Sovereign Enclave · GDPR++ v2030.4", "rails": "Stripe BGN (лв) / EUR SEPA · Solana Pay · Base L2 · Paddle MoR", "edge": "Southeast Europe Rosenpass PQ Relay (~22ms Sofia RTT)"},
    "BE": {"code": "BE", "flag": "🇧🇪", "name": "Belgium", "native_name": "België / Belgique", "currency": "EUR", "default_lang": "nl", "languages": ["nl", "fr", "de", "en"], "regime": "APD/GBA GDPR++ · CCB NIS2 Cyber Framework & EU AI Act · GDPR++ v2030.4", "rails": "Stripe EUR (€) Bancontact / SEPA · Solana Pay · Base L2 · Paddle", "edge": "Western Europe Rosenpass PQ Relay (~14ms Brussels RTT)"},
    "NL": {"code": "NL", "flag": "🇳🇱", "name": "The Netherlands", "native_name": "Nederland", "currency": "EUR", "default_lang": "nl", "languages": ["nl", "en"], "regime": "Autoriteit Persoonsgegevens AVG++ · NCSC-NL NIS2 · GDPR++ v2030.4", "rails": "Stripe EUR (€) iDEAL / SEPA / Cards · Solana Pay · Base L2 · Paddle", "edge": "Western Europe Rosenpass PQ Relay (~12ms Amsterdam RTT)"},
    "TR": {"code": "TR", "flag": "🇹🇷", "name": "Turkey", "native_name": "Türkiye", "currency": "TRY", "default_lang": "tr", "languages": ["tr", "en"], "regime": "Turkey KVKK (Law No. 6698) · Post-Quantum Cryptoshredding · GDPR++ v2030.4", "rails": "Stripe TRY (₺) Cards · Solana Pay · Base L2 USDC · Paddle · x402", "edge": "Eurasia TLS 1.3 Edge + EU Rosenpass PQ Relay"},
    "AU": {"code": "AU", "flag": "🇦🇺", "name": "Australia", "native_name": "Australia", "currency": "AUD", "default_lang": "en", "languages": ["en"], "regime": "Australian Privacy Principles (APPs) & ASD Essential Eight · GDPR++ v2030.4", "rails": "Native Stripe AUD (A$) · Solana Pay · Base L2 · Paddle MoR", "edge": "Oceania Edge Ingress + Post-Quantum WireGuard Mesh"},
    "NZ": {"code": "NZ", "flag": "🇳🇿", "name": "New Zealand", "native_name": "New Zealand / Aotearoa", "currency": "NZD", "default_lang": "en", "languages": ["en"], "regime": "New Zealand Privacy Act 2020 (OPC) & NZISM Zero-Trust · GDPR++ v2030.4", "rails": "Stripe NZD (NZ$) Cards · Solana Pay · Base L2 USDC · Paddle MoR", "edge": "Oceania TLS 1.3 Edge + Post-Quantum Sovereign Mesh"},
    "IT": {"code": "IT", "flag": "🇮🇹", "name": "Italy", "native_name": "Italia", "currency": "EUR", "default_lang": "it", "languages": ["it", "en"], "regime": "Garante Privacy GDPR++ · ACN NIS2 & EU AI Act Enclave · GDPR++ v2030.4", "rails": "Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · Paddle MoR", "edge": "Southern Europe Rosenpass PQ Relay (~19ms Milan RTT)"},
    "ES": {"code": "ES", "flag": "🇪🇸", "name": "Spain", "native_name": "España", "currency": "EUR", "default_lang": "es", "languages": ["es", "en"], "regime": "AEPD LOPDGDD++ · CCN-CERT ENS & NIS2 Sovereign Enclave · GDPR++ v2030.4", "rails": "Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · Paddle MoR", "edge": "Iberian Rosenpass PQ Relay (~24ms Madrid RTT)"},
    "CY": {"code": "CY", "flag": "🇨🇾", "name": "Cyprus", "native_name": "Κύπρος / Kıbrıs", "currency": "EUR", "default_lang": "el", "languages": ["el", "tr", "en"], "regime": "Cyprus Commissioner GDPR++ · DSA Cyber-Security & NIS2 · GDPR++ v2030.4", "rails": "Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · Paddle MoR", "edge": "Eastern Med TLS 1.3 Edge + EU Rosenpass PQ Relay"},
    "GR": {"code": "GR", "flag": "🇬🇷", "name": "Greece", "native_name": "Ελλάδα", "currency": "EUR", "default_lang": "el", "languages": ["el", "en"], "regime": "HDPA (ΑΠΔΠΧ) GDPR++ · NCSA Greece NIS2 & EU AI Act · GDPR++ v2030.4", "rails": "Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · Paddle MoR", "edge": "Southeast Europe Rosenpass PQ Relay (~26ms Athens RTT)"},
    "MT": {"code": "MT", "flag": "🇲🇹", "name": "Malta", "native_name": "Malta", "currency": "EUR", "default_lang": "mt", "languages": ["mt", "en"], "regime": "IDPC Malta GDPR++ · MDIA Digital Assurance & DORA/NIS2 · GDPR++ v2030.4", "rails": "Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · Paddle MoR", "edge": "Mediterranean TLS 1.3 Edge + EU Rosenpass PQ Relay"},
    "ZA": {"code": "ZA", "flag": "🇿🇦", "name": "South Africa", "native_name": "South Africa", "currency": "ZAR", "default_lang": "en", "languages": ["en"], "regime": "South Africa POPIA (Information Regulator) · Zero-Trust Enclave · GDPR++ v2030.4", "rails": "Stripe ZAR (R) Cards · Solana Pay · Base L2 USDC · Paddle · x402", "edge": "Southern Africa Anycast Edge + EU Post-Quantum Relay"},
    "AE": {"code": "AE", "flag": "🇦🇪", "name": "United Arab Emirates", "native_name": "الإمارات العربية المتحدة", "currency": "AED", "default_lang": "ar", "languages": ["ar", "en"], "regime": "UAE Federal PDPL (Decree-Law 45) · ADGM / DIFC Sovereign Enclave · GDPR++ v2030.4", "rails": "Stripe AED Cards · Solana Pay · Base L2 USDC · Paddle · Agentic x402", "edge": "Gulf Sovereign TLS 1.3 Edge + Post-Quantum Rosenpass Mesh"},
    "SA": {"code": "SA", "flag": "🇸🇦", "name": "Saudi Arabia", "native_name": "المملكة العربية السعودية", "currency": "SAR", "default_lang": "ar", "languages": ["ar", "en"], "regime": "Saudi SDAIA PDPL & NCA Essential Cybersecurity Controls (ECC) · GDPR++ v2030.4", "rails": "Stripe SAR Cards · Solana Pay · Base L2 USDC · Paddle · Agentic x402", "edge": "Gulf Sovereign TLS 1.3 Edge + Post-Quantum Rosenpass Mesh"},
}

for _mk, _mval in MARKETS_42.items():
    _mval["lang"] = _mval["default_lang"]
    _mval["dir"] = LANGUAGES_25[_mval["default_lang"]]["dir"]

# ---------------------------------------------------------------------------
# 4. INVARIANT TECHNICAL & REGULATORY TOKENS (Protected Across All 25 Langs)
# ---------------------------------------------------------------------------
PROTECTED_LITERALS: List[str] = sorted(
    [
        "RASA-X-MACHINA OÜ",
        "RASA-X-MACHINA",
        "Rasa-X-Machina",
        "TianxiaOS",
        "Collins Takem",
        "Ndimmôrwyn",
        "Ndimmorwyn",
        "Faery Fortress",
        "Veritas-Rex",
        "TetraLedger",
        "Aethervault",
        "NomenAgora",
        "ETAMANGA",
        "Etamanga",
        "RasaXM",
        "JobMatch",
        "Murua",
        "MANAS",
        "VRTTI",
        "KAI³",
        "KAI3",
        "ENHAN³",
        "SLECO-SO++",
        "Daśavidyāyāna",
        "Dasavidyayana",
        "DSS-14.2",
        "DSS-14",
        "GDPR++",
        "DSGVO++",
        "RGPD++",
        "§ 100¹",
        "#179423",
        "Välismaalaste seadus",
        "Dealum",
        "Rosenpass",
        "WireGuard",
        "Tailscale",
        "NixOS",
        "seL4",
        "VirtWL",
        "AF_XDP",
        "eBPF",
        "XChaCha20-Poly1305",
        "ML-KEM-1024",
        "ERC-8004",
        "x402",
        "$ETMA",
        "$EFM",
        "ETMA10",
        "EFM10",
        "Solana Pay",
        "Base L2",
        "Gumroad",
        "Paddle MoR",
        "Crossmint",
        "Skyfire",
        "DeFiLlama",
        "Jito-Solana",
        "Flashbots",
        "MarginFi",
        "Kamino",
        "Aerodrome",
        "Raydium",
        "Basescan",
        "Pump.fun",
        "WebGPU",
        "WebAuthn",
        "FIDO2",
        "CISA KEVs",
        "CISA KEV",
        "Feodo",
        "CN08",
        "TalTech",
        "Startup Estonia",
        "Tehnopol",
        "Superangel",
        "Startup Wise Guys",
        "EstBAN",
        "Garage48",
        "latitude-tianxia",
        "tianxia-relay",
        "pixel8pro",
        "poco-x5-pro-5g",
        "tx_tui.py --once",
        "tx_tui.py",
        "tx_opportunities_miner",
        "tx_scour",
        "navigator.gpu",
        "TIANXIAOS",
        "VERITAS-REX",
        "CROWNFORGE",
        "Crownforge",
        "LionsOS",
        "Nanos",
        "CycloneDX",
        "Ed25519",
        "OpenSSL",
        "SHA256SUMS",
        "xps13-tianxia",
        "Isikuandmete kaitse seadus",
        "Mahāvidyā",
        "WCAG 2.2 AA",
        "RFC 9116",
        "SO_PEERCRED",
        "Pactum AI",
        "Blackwall",
        "BotGuard",
        "Itella Smartpost",
        "Deutsche Post DHL",
        "Chronopost",
        "PostNL",
    ],
    key=len,
    reverse=True,
)

PROTECTED_REGEXES: List[re.Pattern] = [
    re.compile(r"https?://[^\s<>\"')]+"),
    re.compile(r"wss?://[^\s<>\"')]+"),
    re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    re.compile(r"\b[a-z0-9_-]+@[a-z0-9_-]+:[~$#]+"),
    re.compile(r"\b(?:[a-z0-9-]+\.)?(?:rasaxmachina\.com|ts\.net|aki\.ee|e2b\.dev)(?:/[a-zA-Z0-9_./-]*)?"),
    re.compile(r"/(?:api/v1|dev/shm|run/tianxia|pricing\.json)[^\s<>\"')]*"),
    re.compile(r"\b[a-f0-9]{32,64}\b"),
    re.compile(r"\b0x[a-fA-F0-9]{6,}\b"),
    re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,}\b"),
    re.compile(r"\b(?:pri|pro|prod)_[a-zA-Z0-9.]+\b"),
    re.compile(r"\b(?:Ctrl\+|Cmd\+|Alt\s*\+\s*)[A-Za-z0-9+]+\b"),
    re.compile(r"\bWS\s+[1-9]\b"),
    re.compile(r"RASAXMACHINA\s*\*\s*\[SKU\]"),
    re.compile(r"\bRASAXMACHINA\s+[A-Z0-9]+\b"),
    re.compile(r"\bSKU-TX-\d+[A-Z]?(?:\.\.\d+)?\b"),
    re.compile(r"(?:CA\$|HK\$|MX\$|CLP\$|AR\$|COL\$|NZ\$|A\$|S\$|[€$£¥₹₩₫₦₺])\s?\d[\d,.]*[kKmMbB]?\+?"),
    re.compile("|".join(re.escape(lit) for lit in PROTECTED_LITERALS)),
]

# Non-translatable English technical acronyms/units that do not count as untranslated prose on their own
PURE_TECH_TOKENS: Set[str] = {
    "api", "cli", "tui", "gui", "hud", "os", "ai", "llm", "opex", "arr", "mrr",
    "tam", "sam", "som", "rgu", "rgus", "ffp", "ffps", "sku", "skus", "sla",
    "tls", "mtls", "dns", "rpc", "json", "jsonl", "wasm", "simd", "avx2", "cpu",
    "gpu", "ram", "gb", "tb", "mb", "kb", "ms", "rtt", "mpps", "bps", "apy",
    "tvl", "dex", "cex", "mev", "otc", "poa", "dag", "ast", "hsm", "tpm", "pq",
    "ssrf", "cve", "cves", "nvd", "kev", "kevs", "c2", "inr", "upu", "tth",
    "aov", "cv", "b2b", "b2g", "icp", "safe", "ip", "hq", "holdco", "mvp",
    "sepa", "swift", "iban", "vat", "mor", "m2m", "http", "https", "utc", "eet",
    "esc", "ctrl", "cmd", "apk", "exe", "arm64", "x86_64", "linux", "windows",
    "android", "github", "stripe", "solana", "ethereum", "metamask", "coinbase",
    "telegram", "ton", "spl", "sol", "usdc", "usdt", "eth", "btc",
    "eur", "usd", "gbp", "chf", "sek", "nok", "sgd", "jpy", "hkd", "cad",
    "vnd", "krw", "ngn", "kes", "brl", "mxn", "clp", "ars", "cop", "inr",
    "pkr", "pln", "bgn", "try", "aud", "nzd", "zar", "aed", "sar",
    "ee", "de", "fr", "gb", "us", "ch", "se", "no", "sg", "jp", "eu",
    "hk", "ca", "vn", "kr", "ng", "ke", "br", "mx", "cl", "ar", "co", "in",
    "pk", "pl", "fi", "lt", "bg", "be", "nl", "tr", "au", "nz", "it", "es",
    "cy", "gr", "mt", "za", "ae", "sa", "uk", "dach", "anz", "apac", "eea",
    "cee", "latam", "tallinn", "harjumaa", "estonia", "oled", "sha", "ss58",
    "p2p", "v2030", "stmt", "hw", "id", "uri", "url", "fqdn", "loc", "ut",
    "wcag", "aa", "rfc", "posix", "ocaml", "sbom", "cyclonedx", "ed25519",
    "openssl", "sha256sums", "pubkey", "aarch64", "pe32", "elf", "vt100",
    "kyc", "aml", "sig", "crvusd", "busd1", "apyusd", "acar", "veritas",
    "veranta", "mahāvidyā", "crownforge", "lionsos", "nanos", "flashbots",
    "jito", "dhl", "dpd", "postnl", "chronopost", "gls", "itella", "smartpost",
    "postfach", "hbf", "rae", "hub", "dell", "xps", "ubuntu", "nix", "poco",
    "snapdragon", "alt", "ws", "vs", "efm", "etma", "erc", "e2b",
}

# Native locale option labels that are intentionally multilingual self-names
LOCALE_SELF_LABEL_RE = re.compile(r"^[\U0001F1E6-\U0001F1FF]{2}\s+[A-Z]{2}\s+·\s+.+$")

# Money regexes matching `tx_web_standards.js` `tagInlineMoneyNodes()`
PRICE_RE_JS = re.compile(r"([€$])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)([kKmM])?(?!\w)")
PRICE_RE_EXT = re.compile(r"([€$])(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)([kKmMbB])?(?!\w)")

# ---------------------------------------------------------------------------
# 5. CURATED UI KEYS & REUSABLE PATTERNS SPECIFICATION
# ---------------------------------------------------------------------------
EN_UI_SPEC: Dict[str, str] = {
    "skip_main": "Skip to main content",
    "ctx_active": "Active Jurisdiction & Localization",
    "ctx_regime": "Compliance",
    "ctx_rails": "Settlement",
    "ctx_stmt": "Card Descriptor",
    "select_market_lang": "Select Country and Interface Language",
    "select_currency": "Select Display and Billing Currency",
    "dock_apps": "28 Apps",
    "dock_gui": "GUI",
    "dock_hw": "HW",
    "dock_gdpr": "GDPR++",
    "flagship_portal": "Flagship Portal",
    "storefront": "Storefront",
    "fortress_market": "Fortress Market",
    "pay_hub": "Multi-Rail Payment Hub",
    "cockpit_hud": "Cockpit HUD",
    "estonia_companion": "Estonia Committee Companion",
    "architecture_sprints": "Architecture Sprints",
    "reality_ledger": "Reality Ledger",
    "founder_profile": "Founder Profile",
    "terms": "Terms",
    "privacy": "Privacy",
    "gdpr_btn": "🛡️ GDPR++ Horizon Rights (<50ms PQ Cryptoshredding)",
    "gdpr_title": "🛡️ GDPR++ Horizon Data Sovereignty Portal (v2030.4)",
    "gdpr_email_label": "Subject Email Address *",
    "gdpr_right_label": "Select GDPR++ Sovereign Right *",
    "gdpr_art15": "Art. 15++ — Zero-Knowledge Cryptographic Access Audit",
    "gdpr_art17": "Art. 17++ — <50ms Post-Quantum Ephemeral Key Cryptoshredding",
    "gdpr_art20": "Art. 20++ — Signed JSON-LD Data Portability Export",
    "gdpr_art21": "Art. 21++ / EU AI Act Art. 86 — Automated AI Inference Opt-Out",
    "gdpr_submit": "Execute GDPR++ Request & Issue Merkle Proof ↗",
    "gdpr_executing": "Executing Post-Quantum Envelope Operation...",
    "hw_btn": "⚡ Hardware Enclave Bridge",
    "hw_title": "⚡ Sovereign Polyglot Web App Hardware Bridge (Opt-In)",
    "hw_webgpu_btn": "Probe WebGPU",
    "hw_webauthn_btn": "Verify Enclave",
    "hw_wakelock_btn": "Toggle WakeLock",
    "hw_idle": "Hardware Status: Idle (Zero permissions requested until clicked).",
    "cmdk_btn": "⌘K Ecosystem Launcher (28 Subdomains)",
    "cmdk_placeholder": "Jump to any of 28 Subdomains, GitHub, TUI CLI, Cockpit GUI...",
    "cmdk_surfaces_label": "4 Cohesive Surfaces:",
    "run_live_check": "Run Live Check",
    "execute_query": "Execute Query",
    "verify_merkle_proof": "Verify Merkle Proof",
    "download_executables": "Download Signed Executables",
    "dl_linux": "Linux (x86_64 / ARM64)",
    "dl_windows": "Windows (x86_64 .exe)",
    "dl_android": "Android (Signed APK & ARM64)",
    "status": "Status",
    "latency": "Latency",
    "result": "Result",
    "copy": "Copy",
    "copied": "Copied!",
    "reset": "Reset",
    "clear": "Clear",
    "close": "Close",
    "search": "Search",
    "filter": "Filter",
    "launch": "Launch ↗",
    "inspect": "Inspect",
    "try_again": "Try Again",
    "per_month": "/ month",
    "per_mo_short": "/ mo",
    "perpetual_license": "perpetual license",
    "one_time_license": "one-time license",
    "pay_with_stripe": "💳 Pay with Stripe ↗",
    "buy_on_gumroad": "📦 Buy on Gumroad ↗",
    "pay_multi_rail": "Pay via Solana / Base L2 / 6 Rails (-10%) ↗",
    "scope_vrtti_sprint": "🏛️ Scope Custom VRTTI Sprint ↗",
    "back_main_storefront": "← Main Storefront (21 SKUs)",
    "creating_session": "Creating Live Multi-Rail Session...",
    "session_ready": "Checkout Session Ready ✓",
}

REUSABLE_PATTERN_SPECS: List[dict] = [
    {"id": "subscribe_to", "regex": r"^Subscribe to\s+(.+)$", "en": "Subscribe to ⟦90⟧", "en_tpl": "Subscribe to {0}"},
    {"id": "acquire_colon", "regex": r"^Acquire:\s*(.+)$", "en": "Acquire: ⟦90⟧", "en_tpl": "Acquire: {0}"},
    {"id": "acquire_item", "regex": r"^Acquire\s+(.+)$", "en": "Acquire ⟦90⟧", "en_tpl": "Acquire {0}"},
    {"id": "book_colon", "regex": r"^Book:\s*(.+)$", "en": "Schedule: ⟦90⟧", "en_tpl": "Book: {0}"},
    {"id": "buy_btn_amt", "regex": r"^💳\s*Buy\s*\((.+)\)\s*↗$", "en": "💳 Buy (⟦90⟧) ↗", "en_tpl": "💳 Buy ({0}) ↗"},
    {"id": "pay_btn_amt", "regex": r"^💳\s*Pay\s+(.+)\s*↗$", "en": "💳 Pay ⟦90⟧ ↗", "en_tpl": "💳 Pay {0} ↗"},
    {"id": "gen_checkout_curr", "regex": r"^Generate Live\s+([A-Z]{3})\s+Checkout Session & Seal Receipt ↗$", "en": "Generate Live ⟦90⟧ Checkout Session & Seal Receipt ↗", "en_tpl": "Generate Live {0} Checkout Session & Seal Receipt ↗"},
    {"id": "exploited_cves", "regex": r"^([\d,.\s]+)\s+Exploited CVEs$", "en": "⟦90⟧ Exploited CVEs", "en_tpl": "{0} Exploited CVEs"},
    {"id": "active_exploited_cves", "regex": r"^([\d,.\s]+)\s+Active Exploited CVEs$", "en": "⟦90⟧ Active Exploited CVEs", "en_tpl": "{0} Active Exploited CVEs"},
    {"id": "c2_sinkholed", "regex": r"^([\d,.\s]+)\s+C2 Nodes Sinkholed$", "en": "⟦90⟧ C2 Nodes Sinkholed", "en_tpl": "{0} C2 Nodes Sinkholed"},
    {"id": "feodo_sinkholed", "regex": r"^([\d,.\s]+)\s+Feodo C2 Botnets Sinkholed$", "en": "⟦90⟧ Feodo C2 Botnets Sinkholed", "en_tpl": "{0} Feodo C2 Botnets Sinkholed"},
    {"id": "discrepancy_amt", "regex": r"^(.+)\s+Discrepancy$", "en": "⟦90⟧ Discrepancy", "en_tpl": "{0} Discrepancy"},
    {"id": "track_lbl", "regex": r"^Track:\s*(.+)$", "en": "Track: ⟦90⟧", "en_tpl": "Track: {0}"},
    {"id": "topology_lbl", "regex": r"^Topology:\s*(.+)$", "en": "Topology: ⟦90⟧", "en_tpl": "Topology: {0}"},
    {"id": "standard_lbl", "regex": r"^Standard:\s*(.+)$", "en": "Standard: ⟦90⟧", "en_tpl": "Standard: {0}"},
    {"id": "spec_title", "regex": r"^(.+)\s*·\s*Specification$", "en": "⟦90⟧ · Specification", "en_tpl": "{0} · Specification"},
    {"id": "items_count", "regex": r"^([\d,.\s]+)\s+items$", "en": "⟦90⟧ items", "en_tpl": "{0} items"},
    {"id": "nodes_count", "regex": r"^([\d,.\s]+)\s+Nodes$", "en": "⟦90⟧ Nodes", "en_tpl": "{0} Nodes"},
    {"id": "currencies_active", "regex": r"^(\d+)\s+Currencies Active$", "en": "⟦90⟧ Currencies Active", "en_tpl": "{0} Currencies Active"},
]

# Curated single-word cognate overrides where GTX sometimes returns the English loanword
CURATED_WORD_OVERRIDES: Dict[str, Dict[str, str]] = {
    "Storefront": {
        "de": "Online-Shop", "fr": "Boutique", "es": "Tienda", "pt": "Loja",
        "it": "Negozio", "nl": "Winkel", "pl": "Sklep", "sv": "Butik", "no": "Butikk",
        "et": "E-pood", "fi": "Verkkokauppa", "lt": "Parduotuvė", "tr": "Mağaza",
        "mt": "Ħanut", "sw": "Duka", "vi": "Cửa hàng",
    },
    "Status": {
        "de": "Systemstatus", "fr": "Statut", "es": "Estado", "pt": "Estado",
        "it": "Stato", "nl": "Systeemstatus", "pl": "Stan", "sv": "Systemstatus",
        "no": "Systemstatus", "et": "Olek", "fi": "Tila", "lt": "Būsena",
        "tr": "Durum", "mt": "Stat", "sw": "Hali", "vi": "Trạng thái",
    },
    "Radar": {
        "et": "Ohuradar", "de": "Bedrohungsradar", "fr": "Radar de menaces",
        "es": "Radar de amenazas", "pt": "Radar de ameaças", "it": "Radar minacce",
        "nl": "Dreigingsradar", "pl": "Radar zagrożeń", "fi": "Uhkatutka",
        "lt": "Grėsmių radaras", "sv": "Hotradar", "no": "Trusselradar",
        "tr": "Tehdit Radarı", "mt": "Radar tat-Theddid", "sw": "Rada ya Vitisho",
        "vi": "Radar mối đe dọa",
    },
    "Compliance": {
        "de": "Rechtskonformität", "fr": "Conformité", "es": "Cumplimiento",
        "pt": "Conformidade", "it": "Conformità", "nl": "Naleving", "pl": "Zgodność",
        "sv": "Efterlevnad", "no": "Samsvar", "et": "Vastavus", "fi": "Vaatimustenmukaisuus",
        "lt": "Atitiktis", "tr": "Uyumluluk", "mt": "Konformità", "sw": "Uzingatiaji",
        "vi": "Tuân thủ",
    },
    "Audit": {
        "de": "Sicherheitsprüfung", "fr": "Vérification", "es": "Auditoría",
        "pt": "Auditoria", "it": "Revisione", "nl": "Controle", "pl": "Audyt",
        "sv": "Granskning", "no": "Revisjon", "et": "Audiitorkontroll",
        "fi": "Auditointi", "lt": "Auditas", "tr": "Denetim", "mt": "Verifika",
        "sw": "Ukaguzi", "vi": "Kiểm toán",
    },
    "Portal": {
        "de": "Hauptportal", "fr": "Portail", "es": "Portal soberano",
        "pt": "Portal soberano", "it": "Portale", "nl": "Portaal", "pl": "Portal główny",
        "sv": "Webbportal", "no": "Nettportal", "et": "Portaal", "fi": "Portaali",
        "lt": "Portalas", "tr": "Geçit Portalı", "mt": "Portal", "sw": "Lango",
        "vi": "Cổng thông tin",
    },
    "Telemetry": {
        "de": "Telemetrie", "fr": "Télémétrie", "es": "Telemetría", "pt": "Telemetria",
        "it": "Telemetria", "nl": "Telemetrie", "pl": "Telemetria", "sv": "Telemetri",
        "no": "Telemetri", "et": "Telemeetria", "fi": "Telemetria", "lt": "Telemetrija",
        "tr": "Telemetri", "mt": "Telemetrija", "sw": "Telemetri", "vi": "Viễn trắc",
    },
    "Cockpit": {
        "et": "Juhtpaneel", "es": "Cabina de control", "pt": "Painel de controle",
        "it": "Cabina di regia", "nl": "Bedieningspaneel", "pl": "Kokpit",
        "fi": "Ohjaamo", "lt": "Valdymo pultas", "tr": "Kokpit", "mt": "Kabina",
        "sw": "Chumba cha udhibiti", "vi": "Buồng lái điều khiển",
    },
    "Terminal": {
        "de": "Konsole", "fr": "Console", "es": "Consola", "pt": "Console",
        "it": "Terminale", "nl": "Console", "pl": "Konsola", "sv": "Konsol",
        "no": "Konsoll", "et": "Käsurida", "fi": "Pääte", "lt": "Terminalas",
        "tr": "Uçbirim", "mt": "Terminal", "sw": "Kituo cha amri", "vi": "Thiết bị đầu cuối",
    },
    "Global": {
        "de": "Weltweit", "fr": "Mondial", "es": "Mundial", "pt": "Mundial",
        "it": "Globale", "nl": "Wereldwijd", "pl": "Globalny", "sv": "Globalt",
        "no": "Globalt", "et": "Ülemaailmne", "fi": "Maailmanlaajuinen",
        "lt": "Pasaulinis", "tr": "Küresel", "mt": "Globali", "sw": "Kimataifa",
        "vi": "Toàn cầu",
    },
    "Sprints": {
        "de": "Entwicklungszyklen", "fr": "Cycles intensifs", "es": "Ciclos intensivos",
        "pt": "Ciclos intensivos", "it": "Cicli intensivi", "nl": "Ontwikkelsprints",
        "pl": "Cykle wdrożeniowe", "sv": "Utvecklingssprintar", "no": "Utviklingssprinter",
        "et": "Arendussprindid", "fi": "Kehityssprintit", "lt": "Diegimo ciklai",
        "tr": "Uygulama Döngüleri", "mt": "Ċikli ta' Żvilupp", "sw": "Awamu za Utekelezaji",
        "vi": "Chu kỳ triển khai",
    },
    "VRTTI Sprints": {
        "de": "VRTTI-Entwicklungszyklen", "fr": "Cycles VRTTI", "es": "Ciclos VRTTI",
        "pt": "Ciclos VRTTI", "it": "Cicli VRTTI", "nl": "VRTTI-sprints",
        "pl": "Cykle VRTTI", "sv": "VRTTI-sprintar", "no": "VRTTI-sprinter",
        "et": "VRTTI arendussprindid", "fi": "VRTTI-sprintit", "lt": "VRTTI ciklai",
        "tr": "VRTTI Döngüleri", "mt": "Ċikli VRTTI", "sw": "Awamu za VRTTI",
        "vi": "Chu kỳ VRTTI",
    },
    "/ sprint": {
        "de": "/ Zyklus", "fr": "/ cycle", "es": "/ ciclo", "pt": "/ ciclo",
        "it": "/ ciclo", "nl": "/ cyclus", "pl": "/ cykl", "sv": "/ sprintcykel",
        "no": "/ sprintsyklus", "et": "/ sprinttsükkel", "fi": "/ jakso", "lt": "/ ciklas",
        "tr": "/ döngü", "mt": "/ ċiklu", "sw": "/ awamu", "vi": "/ chu kỳ",
    },
    "/sprint": {
        "de": "/Zyklus", "fr": "/cycle", "es": "/ciclo", "pt": "/ciclo",
        "it": "/ciclo", "nl": "/cyclus", "pl": "/cykl", "sv": "/sprintcykel",
        "no": "/sprintsyklus", "et": "/sprinttsükkel", "fi": "/jakso", "lt": "/ciklas",
        "tr": "/döngü", "mt": "/ċiklu", "sw": "/awamu", "vi": "/chu kỳ",
    },
    "Audio": {
        "de": "Tonausgabe", "fr": "Son", "es": "Sonido", "pt": "Áudio",
        "it": "Sonoro", "nl": "Geluid", "pl": "Dźwięk", "sv": "Ljud",
        "no": "Lyd", "et": "Heli", "fi": "Ääni", "lt": "Garsas",
        "tr": "Ses", "mt": "Awdjo", "sw": "Sauti", "vi": "Âm thanh",
    },
}


# ---------------------------------------------------------------------------
# 6. ATOMIC JSON WRITER (SLECO-SO++ Pillar 3.6)
# ---------------------------------------------------------------------------
def atomic_write_json(path: Path, payload: dict) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    encoded = raw.encode("utf-8")
    tmp.write_bytes(encoded)
    os.replace(str(tmp), str(path))
    return len(encoded)


# ---------------------------------------------------------------------------
# 7. PRICING.JSON 29-CURRENCY & 42-MARKET COMPILER
# ---------------------------------------------------------------------------
def round_clean_price(eur_amount: float, curr_code: str) -> float | int:
    cmeta = CURRENCIES_29[curr_code]
    raw = eur_amount * cmeta["rate"]
    if curr_code == "EUR":
        return int(eur_amount) if float(eur_amount).is_integer() else round(eur_amount, 2)
    if cmeta["zero_decimal"]:
        if raw >= 100000:
            return int(round(raw / 1000.0) * 1000)
        if raw >= 1000:
            return int(round(raw / 100.0) * 100)
        return max(1, int(round(raw / 10.0) * 10))
    if raw >= 50000:
        return int(round(raw / 100.0) * 100)
    if raw >= 2000:
        return int(round(raw / 10.0) * 10)
    if raw >= 200:
        return int(round(raw / 5.0) * 5)
    return max(1, int(round(raw)))


def compile_pricing_json() -> dict:
    existing = json.loads(PRICING_PATH.read_text(encoding="utf-8"))
    existing["i18n_version"] = "9.0.0-42markets-29currencies-25langs"
    existing["base_currency"] = "EUR"
    existing["fx_rates"] = {k: v["rate"] for k, v in CURRENCIES_29.items()}
    existing["currencies"] = CURRENCIES_29
    existing["supported_currencies"] = CURRENCIES_29
    existing["markets"] = MARKETS_42
    existing["languages"] = {
        k: {
            "lang": v["lang"],
            "dir": v["dir"],
            "name": v["name"],
            "native_name": v["native_name"],
            "markets": v["markets"],
        }
        for k, v in LANGUAGES_25.items()
    }

    for _plan_key, plan in existing.get("plans", {}).items():
        eur_base = float(plan.get("eur_amount") or 29.0)
        pbc = dict(plan.get("prices_by_currency") or {})
        for curr_code in CURRENCIES_29:
            if curr_code not in pbc:
                pbc[curr_code] = round_clean_price(eur_base, curr_code)
        # Order deterministically in canonical 29-currency sequence
        plan["prices_by_currency"] = {c: pbc[c] for c in CURRENCIES_29}

    sz = atomic_write_json(PRICING_PATH, existing)
    LOG.info(
        "Compiled pricing.json (%d bytes): %d currencies, %d markets, %d languages, %d plan entries.",
        sz,
        len(existing["currencies"]),
        len(existing["markets"]),
        len(existing["languages"]),
        len(existing.get("plans", {})),
    )
    return existing


# ---------------------------------------------------------------------------
# 8. HTML, ATTRIBUTE & DYNAMIC JS TEMPLATE STRING EXTRACTOR
# ---------------------------------------------------------------------------
SKIP_HTML_TAGS: Set[str] = {"script", "style", "code", "pre", "svg", "noscript"}
TRANSLATABLE_ATTRS: Set[str] = {"placeholder", "title", "aria-label", "alt"}


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def split_money_fragments(s: str) -> List[str]:
    frags: List[str] = []
    for rx in (PRICE_RE_JS, PRICE_RE_EXT):
        if rx.search(s):
            parts = rx.split(s)
            for idx in range(0, len(parts), 4):
                f = norm_ws(parts[idx])
                if f and re.search(r"[A-Za-z]", f):
                    frags.append(f)
    return frags


class DOMStringExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: List[str] = []
        self.strings: Set[str] = set()

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        self.stack.append(t)
        ad = {k.lower(): v for k, v in attrs if v}
        if t == "meta":
            mname = ad.get("name", "").lower()
            mprop = ad.get("property", "").lower()
            if (mname in ("description", "twitter:title", "twitter:description") or mprop in ("og:title", "og:description")) and ad.get("content"):
                self._record(ad["content"])
        for ak in TRANSLATABLE_ATTRS:
            if ak in ad:
                self._record(ad[ak])
        if t == "input" and ad.get("type", "").lower() in ("submit", "button") and ad.get("value"):
            self._record(ad["value"])

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        for idx in range(len(self.stack) - 1, -1, -1):
            if self.stack[idx] == t:
                self.stack = self.stack[:idx]
                break

    def handle_data(self, data: str) -> None:
        if any(st in SKIP_HTML_TAGS for st in self.stack):
            return
        self._record(data)

    def _record(self, raw: str) -> None:
        n = norm_ws(raw)
        if not n or not re.search(r"[A-Za-z]", n):
            return
        if "${" in n:
            return
        self.strings.add(n)
        for frag in split_money_fragments(n):
            if "${" not in frag:
                self.strings.add(frag)


def strip_js_interpolations(tpl: str) -> str:
    """Replace balanced ${...} in JS template literals with <code></code> to preserve DOM text splits."""
    out: List[str] = []
    i = 0
    n = len(tpl)
    while i < n:
        if i + 1 < n and tpl[i] == "$" and tpl[i + 1] == "{":
            depth = 1
            i += 2
            while i < n and depth > 0:
                if tpl[i] == "{":
                    depth += 1
                elif tpl[i] == "}":
                    depth -= 1
                i += 1
            out.append("<code></code>")
        else:
            out.append(tpl[i])
            i += 1
    return "".join(out)


def extract_html_files_strings() -> Tuple[Set[str], Dict[str, Set[str]]]:
    """Extract strictly from all *.html files (used both for compilation and 100% coverage verification)."""
    all_html_strings: Set[str] = set()
    per_file: Dict[str, Set[str]] = {}
    for p_str in sorted(glob.glob(str(UI_DIR / "*.html"))):
        p = Path(p_str)
        txt = p.read_text(encoding="utf-8")
        ex = DOMStringExtractor()
        ex.feed(txt)
        per_file[p.name] = ex.strings
        all_html_strings |= ex.strings
    return all_html_strings, per_file


def harvest_existing_curated_translations() -> Dict[str, Dict[str, str]]:
    """Reuse human-curated translations already present in tx_web_standards.js and HTML portals."""
    curated: Dict[str, Dict[str, str]] = {lg: {} for lg in LANGUAGES_25 if lg != "en"}
    ws_path = UI_DIR / "tx_web_standards.js"
    if ws_path.exists():
        ws_txt = ws_path.read_text(encoding="utf-8")
        # Harvest GLOBAL_I18N.<lang>.phrases
        for lg in ("et", "de", "fr", "sv", "no", "ja"):
            m = re.search(rf"\b{lg}:\s*\{{.*?phrases:\s*\{{(.*?)\}}", ws_txt, flags=re.S)
            if m:
                for k, v in re.findall(r"'([^']+)'\s*:\s*'((?:\\'|[^'])+)'", m.group(1)):
                    ck = norm_ws(k)
                    cv = norm_ws(v.replace("\\'", "'"))
                    if ck and cv:
                        curated[lg][ck] = cv
    return curated


def extract_dynamic_js_and_config_strings() -> Set[str]:
    """Extract dynamic strings from inline <script> catalogs, tx_web_standards.js, subdomains.json & pricing.json."""
    dyn: Set[str] = set()

    def add_str(raw: str) -> None:
        if "<" in raw and ">" in raw:
            ex = DOMStringExtractor()
            ex.feed(raw)
            dyn.update(ex.strings)
        n = norm_ws(re.sub(r"<[^>]+>", " ", raw))
        if n and re.search(r"[A-Za-z]", n) and "${" not in n:
            dyn.add(n)
            for frag in split_money_fragments(n):
                dyn.add(frag)

    # 1. Curated UI spec & interactive console labels
    for val in EN_UI_SPEC.values():
        add_str(val)

    extra_console_phrases = [
        "Run Live Check", "Execute Query", "Verify Merkle Proof",
        "Download Signed Executables", "Linux (x86_64 / ARM64)",
        "Windows (x86_64 .exe)", "Android (Signed APK & ARM64)",
        "Status", "Latency", "Result", "Copy", "Copied!", "Reset", "Clear",
        "Pay via Solana / Base L2 / 6 Rails (-10%) ↗",
        "🏛️ Scope Custom VRTTI Sprint ↗",
        "← Main Storefront (21 SKUs)",
        "perpetual license", "/ month", "/ mo", "one-time", "perpetual", "escrow",
        "Creating Live Multi-Rail Session...", "Checkout Session Ready ✓",
        "Try Again", "Validating via MANAS System-1 Shield...",
        "Proposal Registered ✓", "No subdomains match the filter criteria.",
        "📑 Show All 12 Slides at Once", "🎯 Single Slide View",
        "← Previous Slide", "Next Slide →", "Copy Text",
        "Copy Full 9-Step Record", "Loading Merkle root...",
        "⚡ System Actions", "🤖 Swarm Agents",
        "💰 Revenue Generating Units (RGUs)",
        "🌐 Sovereign Subdomains (28 Governed Portals)",
        "No matching commands, agents, RGUs, or subdomains.",
        "No RGUs found.", "No RGUs match the filter.",
        "Select Market & Language", "Select Currency",
        "All Markets", "Language", "Market", "Currency",
    ]
    for ph in extra_console_phrases:
        add_str(ph)

    # 2. All 42 market names, regimes, rails, edge descriptions
    for mmeta in MARKETS_42.values():
        add_str(mmeta["name"])
        add_str(mmeta["regime"])
        add_str(mmeta["rails"])
        add_str(mmeta["edge"])

    # 3. subdomains.json & pricing.json
    if SUBDOMAINS_CFG_PATH.exists():
        sd = json.loads(SUBDOMAINS_CFG_PATH.read_text(encoding="utf-8"))
        for rdesc in sd.get("routing_modes", {}).values():
            add_str(rdesc)
        for sinfo in sd.get("subdomains", {}).values():
            if sinfo.get("name"):
                add_str(sinfo["name"])
            if sinfo.get("description"):
                add_str(sinfo["description"])

    if PRICING_PATH.exists():
        pr = json.loads(PRICING_PATH.read_text(encoding="utf-8"))
        for pinfo in pr.get("plans", {}).values():
            if pinfo.get("name"):
                add_str(pinfo["name"])
            if pinfo.get("description"):
                add_str(pinfo["description"])

    # 4. Template literals & data properties inside tx_web_standards.js and HTML <script> tags
    js_sources: List[str] = []
    ws_path = UI_DIR / "tx_web_standards.js"
    if ws_path.exists():
        js_sources.append(ws_path.read_text(encoding="utf-8"))
    for p_str in sorted(glob.glob(str(UI_DIR / "*.html"))):
        htxt = Path(p_str).read_text(encoding="utf-8")
        for sc in re.findall(r"<script\b[^>]*>(.*?)</script>", htxt, flags=re.S | re.I):
            if sc.strip() and not sc.strip().startswith("{"):
                js_sources.append(sc)

    prop_re = re.compile(
        r"\b(?:title|subtitle|name|desc|description|label|cat|badge|tag|h1|lead|dirTitle|badgeRole|badgeStatus|badgeEntity|heroTitle|heroLead|sec[1-6])\s*:\s*(['\"])((?:\\\1|.)*?)\1"
    )
    bullet_block_re = re.compile(r"bullets\s*:\s*\[(.*?)\]", flags=re.S)

    for jsrc in js_sources:
        # Extract HTML template literals
        for raw_tpl in re.findall(r"`([^`]*<[a-zA-Z][^`]*)`", jsrc):
            cleaned_tpl = strip_js_interpolations(raw_tpl)
            ex = DOMStringExtractor()
            ex.feed(cleaned_tpl)
            dyn.update(ex.strings)
        # Extract structured catalog object properties
        for _q, val in prop_re.findall(jsrc):
            unesc = val.replace("\\'", "'").replace('\\"', '"')
            # Skip non-English localized blocks if they have non-ASCII CJK/Cyrillic, keep ASCII/Latin English source
            if not re.search(r"[\u0400-\u04ff\u3040-\u9fff]", unesc):
                add_str(unesc)
        # Extract SLIDES bullets
        for bblock in bullet_block_re.findall(jsrc):
            for _q, bval in re.findall(r"(['\"])((?:\\\1|.)*?)\1", bblock):
                add_str(bval.replace("\\'", "'").replace('\\"', '"'))
        # Extract GLOBAL_I18N.en.phrases keys
        for pk in re.findall(r"'([^'\n]{2,80})'\s*:\s*'", jsrc):
            if re.search(r"[A-Za-z]{2,}", pk) and "_" not in pk:
                add_str(pk)

    return dyn


# ---------------------------------------------------------------------------
# 9. TOKEN PROTECTION & STRUCTURAL WRAPPER DECOMPOSITION (REUSE ENGINE)
# ---------------------------------------------------------------------------
def protect_tokens(text: str) -> Tuple[str, List[str]]:
    """Mask invariant technical, brand, legal, URL, and currency tokens with ASCII-safe ZXTK{idx}Q."""
    tokens: List[str] = []

    def _sub_match(m: re.Match) -> str:
        val = m.group(0)
        if "ZXTK" in val or "⟦" in val or "⟧" in val:
            return val
        idx = len(tokens)
        tokens.append(val)
        return f"ZXTK{idx}Q"

    masked = text
    for rx in PROTECTED_REGEXES:
        masked = rx.sub(_sub_match, masked)
    return masked, tokens


def restore_tokens(translated: str, tokens: List[str]) -> str:
    """Restore masked ZXTK{i}Q tokens (case-insensitive & whitespace-tolerant) and strip any stray math brackets."""
    if not tokens:
        return norm_ws(re.sub(r"[\u27e6\u27e7]+", "", translated))

    def _repl(m: re.Match) -> str:
        idx = int(m.group(1))
        if 0 <= idx < len(tokens):
            return tokens[idx]
        return ""

    restored = re.sub(r"Z\s*X\s*T\s*K\s*(\d+)\s*Q?", _repl, translated, flags=re.IGNORECASE)
    restored = re.sub(r"⟦\s*(\d+)\s*⟧", _repl, restored)
    restored = re.sub(r"[\u27e6\u27e7]+", "", restored)
    for idx, tok in enumerate(tokens):
        if tok not in restored:
            restored = re.sub(rf"\[\s*{idx}\s*\]", lambda _m, t=tok: t, restored)
    return norm_ws(restored)


def has_translatable_english_words(text: str) -> bool:
    """Return True iff `text` contains >=1 natural-language English word outside invariant/tech tokens."""
    if LOCALE_SELF_LABEL_RE.match(text):
        return False
    masked, _ = protect_tokens(text)
    cleaned = re.sub(r"ZXTK\d+Q", " ", masked)
    words = re.findall(r"[A-Za-z]{2,}", cleaned)
    for w in words:
        if w.lower() not in PURE_TECH_TOKENS:
            return True
    return False


# Structural prefix/suffix wrapper splitter for localization element reuse:
# e.g. "⚡ SKU-TX-01 · DIGITAL BLUEPRINT · STMT: RASAXMACHINA 5KBLUEPR"
#   -> prefix="⚡ SKU-TX-01 · ", core="DIGITAL BLUEPRINT", suffix=" · STMT: RASAXMACHINA 5KBLUEPR"
WRAPPER_SKU_RE = re.compile(
    r"^((?:[^\w\s]+\s*)?SKU-TX-\d+[A-Z]?\s*·\s*)(.+?)(\s*·\s*STMT:\s*RASAXMACHINA\s+[A-Z0-9]+)?$"
)
LEADING_WRAP_RE = re.compile(
    r"^((?:[\u2190-\u2bff\u25a0-\u27bf\U0001f300-\U0001faff✓✕⚡🛡️🏛️🛰️💳📦◎🔵⬡🤖🔍📋🇪🇪🇺🇸🇬🇧🇩🇪🇨🇭🇫🇷🇸🇪🇳🇴🇨🇦🇦🇺🇸🇬🇯🇵🐙🖥️⌘»•·\-–—]+\s*)+|\d{1,2}\s*(?:·|//|\.)\s*)"
)
TRAILING_WRAP_RE = re.compile(
    r"(\s*(?:↗|↓|→|←|\(\d+\)|\*)+)$"
)


def decompose_wrapper(s: str) -> Tuple[str, str, str]:
    m_sku = WRAPPER_SKU_RE.match(s)
    if m_sku:
        pre = m_sku.group(1) or ""
        core = m_sku.group(2) or ""
        suf = m_sku.group(3) or ""
        if core and re.search(r"[A-Za-z]", core):
            return pre, core, suf

    pre = ""
    suf = ""
    rem = s
    m_pre = LEADING_WRAP_RE.match(rem)
    if m_pre and len(m_pre.group(1)) < len(rem):
        cand = rem[len(m_pre.group(1)):]
        if re.search(r"[A-Za-z]", cand):
            pre = m_pre.group(1)
            rem = cand

    m_suf = TRAILING_WRAP_RE.search(rem)
    if m_suf and len(m_suf.group(1)) < len(rem):
        cand = rem[: len(rem) - len(m_suf.group(1))]
        if re.search(r"[A-Za-z]", cand):
            suf = m_suf.group(1)
            rem = cand

    return pre, rem, suf


# ---------------------------------------------------------------------------
# 10. PERSISTENT-TLS BATCH TRANSLATION CLIENT (GTX + RETRY + BISECT)
# ---------------------------------------------------------------------------
_TLS_LOCAL = threading.local()
_SSL_CTX = ssl.create_default_context()


def _get_gtx_conn(host: str = "clients5.google.com") -> http.client.HTTPSConnection:
    conns = getattr(_TLS_LOCAL, "conns", None)
    if conns is None:
        conns = {}
        _TLS_LOCAL.conns = conns
    conn = conns.get(host)
    if conn is None:
        conn = http.client.HTTPSConnection(host, timeout=18, context=_SSL_CTX)
        conns[host] = conn
    return conn


def _reset_gtx_conn(host: Optional[str] = None) -> None:
    conns = getattr(_TLS_LOCAL, "conns", None)
    if not conns:
        return
    hosts = [host] if host else list(conns.keys())
    for h in hosts:
        conn = conns.pop(h, None)
        if conn is not None:
            try:
                conn.close()
            except Exception as _exc:
                LOG.debug("close conn: %s", _exc)


def translate_masked_batch(lines: List[str], target_gtx_lang: str) -> List[str]:
    """Translate a batch of masked strings via clients5 multi-q native JSON array (with gtx fallback)."""
    if not lines:
        return []

    path = (
        "/translate_a/t?client=dict-chrome-ex&sl=en&tl="
        + urllib.parse.quote(target_gtx_lang)
    )
    body_bytes = urllib.parse.urlencode([("q", ln) for ln in lines]).encode("utf-8")
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Content-Length": str(len(body_bytes)),
        "Connection": "keep-alive",
    }
    last_err: Optional[Exception] = None
    for attempt in range(5):
        try:
            conn = _get_gtx_conn("clients5.google.com")
            conn.request("POST", path, body=body_bytes, headers=headers)
            resp = conn.getresponse()
            body = resp.read()
            if resp.status != 200:
                _reset_gtx_conn("clients5.google.com")
                time.sleep(0.5 * (2 ** attempt))
                continue
            data = json.loads(body.decode("utf-8"))
            if isinstance(data, list) and len(data) == len(lines):
                out: List[str] = []
                for orig, item in zip(lines, data):
                    if isinstance(item, list) and item:
                        val = str(item[0])
                    elif isinstance(item, str):
                        val = item
                    else:
                        val = orig
                    out.append(val.replace("\n", " ").strip() or orig)
                time.sleep(0.05)
                return out
            if len(lines) == 1 and isinstance(data, str):
                return [data.replace("\n", " ").strip() or lines[0]]
        except Exception as exc:
            last_err = exc
            _reset_gtx_conn("clients5.google.com")
            time.sleep(0.4 * (2 ** attempt))

    LOG.warning("clients5 fallback after retries (%s, n=%d): %s", target_gtx_lang, len(lines), last_err)
    if len(lines) > 1:
        mid = len(lines) // 2
        return translate_masked_batch(lines[:mid], target_gtx_lang) + translate_masked_batch(lines[mid:], target_gtx_lang)
    return list(lines)


def build_batches(items: List[str], max_chars: int = 5200, max_lines: int = 80) -> List[List[str]]:
    batches: List[List[str]] = []
    cur: List[str] = []
    cur_len = 0
    for it in items:
        add_len = len(it) + 1
        if cur and (cur_len + add_len > max_chars or len(cur) >= max_lines):
            batches.append(cur)
            cur = []
            cur_len = 0
        cur.append(it)
        cur_len += add_len
    if cur:
        batches.append(cur)
    return batches


# ---------------------------------------------------------------------------
# 11. FULL 25-LANGUAGE COMPILER & REUSE PIPELINE
# ---------------------------------------------------------------------------
def compile_all_language_packs(max_workers: int = 10, target_langs: Optional[List[str]] = None) -> dict:
    I18N_DIR.mkdir(parents=True, exist_ok=True)

    html_strings, per_html_file = extract_html_files_strings()
    dyn_strings = extract_dynamic_js_and_config_strings()
    all_surface_strings = sorted(html_strings | dyn_strings)

    # Separate invariant/pure-identifier strings vs natural-language strings
    invariant_strings: Set[str] = set()
    natural_strings: List[str] = []
    for s in all_surface_strings:
        if has_translatable_english_words(s):
            natural_strings.append(s)
        else:
            invariant_strings.add(s)

    # Structural decomposition into deduplicated Core Segments!
    surface_to_decomp: Dict[str, Tuple[str, str, str]] = {}
    unique_cores_set: Set[str] = set()
    for s in natural_strings:
        pre, core, suf = decompose_wrapper(s)
        surface_to_decomp[s] = (pre, core, suf)
        unique_cores_set.add(core)

    # Also include pattern templates and country names in the shared core table!
    pattern_en_cores = [p["en"] for p in REUSABLE_PATTERN_SPECS]
    country_en_names = [m["name"] for m in MARKETS_42.values()]
    for pc in pattern_en_cores:
        unique_cores_set.add(pc)
    for cn in country_en_names:
        unique_cores_set.add(cn)
    for uv in EN_UI_SPEC.values():
        _p, uc, _s = decompose_wrapper(uv)
        unique_cores_set.add(uc)

    unique_cores = sorted(unique_cores_set)
    reuse_saved = len(natural_strings) - len(unique_cores)
    LOG.info(
        "Extracted %d total surface strings (%d HTML static/split across %d files + %d dynamic JS/config). "
        "Natural-language: %d -> Decomposed into %d reusable core segments (saved %d redundant segments).",
        len(all_surface_strings),
        len(html_strings),
        len(per_html_file),
        len(all_surface_strings) - len(html_strings),
        len(natural_strings),
        len(unique_cores),
        max(0, reuse_saved),
    )

    # Pre-mask all unique core segments once!
    core_masked_map: Dict[str, Tuple[str, List[str]]] = {}
    for core in unique_cores:
        # Preserve Title Case translation quality for ALL-CAPS short badge cores like "DIGITAL BLUEPRINT"
        norm_core = core.title() if (core.isupper() and len(core) > 4 and " " in core) else core
        masked, toks = protect_tokens(norm_core)
        core_masked_map[core] = (masked, toks)

    curated_harvest = harvest_existing_curated_translations()

    # 1. Emit English (`en.json`) canonical reference pack
    en_patterns = [
        {
            "id": p["id"],
            "regex": p["regex"],
            "en_template": p.get("en_tpl", p["en"].replace("⟦90⟧", "{0}")),
            "template": p.get("en_tpl", p["en"].replace("⟦90⟧", "{0}")),
        }
        for p in REUSABLE_PATTERN_SPECS
    ]
    en_ui = dict(EN_UI_SPEC)
    en_ui["countries"] = {mk: mv["name"] for mk, mv in MARKETS_42.items()}
    en_pack = {
        "lang": "en",
        "dir": "ltr",
        "native_name": "English",
        "ui": en_ui,
        "patterns": en_patterns,
        "strings": {s: s for s in all_surface_strings},
    }
    atomic_write_json(I18N_DIR / "en.json", en_pack)

    # 2. Translate all 24 non-English language packs
    langs_to_build = [
        lg for lg in LANGUAGES_25
        if lg != "en" and (not target_langs or lg in target_langs)
    ]

    for lg_idx, lg in enumerate(langs_to_build, 1):
        t0 = time.time()
        lmeta = LANGUAGES_25[lg]
        gtx_code = lmeta["gtx"]
        out_path = I18N_DIR / f"{lg}.json"

        # Load incremental translation memory if pack already exists
        existing_strings: Dict[str, str] = {}
        if out_path.exists():
            try:
                prev = json.loads(out_path.read_text(encoding="utf-8"))
                existing_strings = prev.get("strings") or {}
            except Exception as _exc:
                LOG.debug("ignoring unreadable %s: %s", out_path, _exc)

        curated_lg = curated_harvest.get(lg, {})
        word_overrides_lg = {k: v[lg] for k, v in CURATED_WORD_OVERRIDES.items() if lg in v}

        # Determine which core segments need GTX translation
        cores_to_fetch: List[str] = []
        core_translations: Dict[str, str] = {}

        for core in unique_cores:
            if core in word_overrides_lg:
                core_translations[core] = word_overrides_lg[core]
            elif core in curated_lg and curated_lg[core] != core:
                core_translations[core] = curated_lg[core]
            elif core in existing_strings and existing_strings[core] and existing_strings[core] != core and not re.search(r"[\u27e6\u27e7]|Z\s*X\s*T\s*K\s*\d", existing_strings[core], re.I):
                core_translations[core] = existing_strings[core]
            elif not has_translatable_english_words(core):
                core_translations[core] = core
            else:
                cores_to_fetch.append(core)

        if cores_to_fetch:
            masked_inputs = [core_masked_map[c][0] for c in cores_to_fetch]
            batches = build_batches(masked_inputs, max_chars=5200, max_lines=80)
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
                batch_results = list(pool.map(lambda b: translate_masked_batch(b, gtx_code), batches))

            flat_translated: List[str] = [item for sub in batch_results for item in sub]
            for core, tr_masked in zip(cores_to_fetch, flat_translated):
                toks = core_masked_map[core][1]
                restored = restore_tokens(tr_masked, toks)
                if core.isupper() and len(core) > 4 and lmeta["dir"] == "ltr":
                    # Preserve badge uppercase styling while keeping invariant tokens intact
                    restored = restored.upper()
                    for tok in toks:
                        restored = re.sub(re.escape(tok.upper()), lambda _m, t=tok: t, restored)
                core_translations[core] = restored or core

        # Reassemble all surface strings from decomposed (prefix + translated_core + suffix)
        strings_map: Dict[str, str] = {}
        for inv in invariant_strings:
            strings_map[inv] = inv

        for s in natural_strings:
            if s in word_overrides_lg:
                strings_map[s] = word_overrides_lg[s]
                continue
            if s in curated_lg and curated_lg[s] != s:
                strings_map[s] = curated_lg[s]
                continue
            pre, core, suf = surface_to_decomp[s]
            tr_core = core_translations.get(core, core)
            assembled = norm_ws(f"{pre}{tr_core}{suf}") if (pre or suf) else tr_core
            strings_map[s] = assembled or s

        # Build `ui` dictionary for `<lang>.json`
        ui_out: Dict[str, object] = {}
        for uk, uval in EN_UI_SPEC.items():
            if uval in strings_map:
                ui_out[uk] = strings_map[uval]
            else:
                upre, ucore, usuf = decompose_wrapper(uval)
                ui_out[uk] = norm_ws(f"{upre}{core_translations.get(ucore, ucore)}{usuf}")
        ui_out["countries"] = {
            mk: core_translations.get(mv["name"], mv["name"])
            for mk, mv in MARKETS_42.items()
        }

        # Build `patterns` array for `<lang>.json`
        patterns_out: List[dict] = []
        for p in REUSABLE_PATTERN_SPECS:
            tr_pat = core_translations.get(p["en"], p["en"])
            tr_tpl = re.sub(r"⟦\s*90\s*⟧", "{0}", tr_pat)
            if "{0}" not in tr_tpl:
                tr_tpl = f"{tr_tpl} {{0}}"
            patterns_out.append(
                {
                    "id": p["id"],
                    "regex": p["regex"],
                    "re": p["regex"],
                    "en_template": p.get("en_tpl", p["en"].replace("⟦90⟧", "{0}")),
                    "template": norm_ws(tr_tpl),
                    "tpl": norm_ws(tr_tpl),
                }
            )

        pack_payload = {
            "lang": lg,
            "dir": lmeta["dir"],
            "native_name": lmeta["native_name"],
            "name": lmeta["name"],
            "markets": lmeta["markets"],
            "ui": ui_out,
            "patterns": patterns_out,
            "strings": strings_map,
        }
        sz = atomic_write_json(out_path, pack_payload)
        dt = time.time() - t0
        LOG.info(
            "[%02d/%02d] Compiled %s (%s, %s) in %.1fs — %d strings, %d patterns, %d KB",
            lg_idx,
            len(langs_to_build),
            out_path.name,
            lmeta["native_name"],
            lmeta["dir"],
            dt,
            len(strings_map),
            len(patterns_out),
            sz // 1024,
        )

    # 3. Write `/tianxia/ui/i18n/index.json` listing all 25 languages, 42 markets, and 29 currencies
    index_payload = {
        "version": "9.0.0-42markets-29currencies-25langs",
        "counts": {
            "languages": len(LANGUAGES_25),
            "markets": len(MARKETS_42),
            "currencies": len(CURRENCIES_29),
            "html_files": len(per_html_file),
            "surface_strings": len(all_surface_strings),
            "reusable_cores": len(unique_cores),
            "patterns": len(REUSABLE_PATTERN_SPECS),
        },
        "languages": {
            lg: {
                "lang": meta["lang"],
                "dir": meta["dir"],
                "name": meta["name"],
                "native_name": meta["native_name"],
                "markets": meta["markets"],
                "pack_url": f"/i18n/{lg}.json",
            }
            for lg, meta in LANGUAGES_25.items()
        },
        "markets": MARKETS_42,
        "currencies": CURRENCIES_29,
    }
    atomic_write_json(I18N_DIR / "index.json", index_payload)
    LOG.info("Wrote i18n/index.json covering 25 languages, 42 markets, and 29 currencies.")
    return index_payload


# ---------------------------------------------------------------------------
# 12. PROGRAMMATIC 100% COVERAGE & QUALITY VERIFIER
# ---------------------------------------------------------------------------
def verify_all_packs() -> dict:
    html_strings, per_file = extract_html_files_strings()
    natural_html_strings = {s for s in html_strings if has_translatable_english_words(s)}

    pricing = json.loads(PRICING_PATH.read_text(encoding="utf-8"))
    idx_data = json.loads((I18N_DIR / "index.json").read_text(encoding="utf-8"))

    assert len(pricing.get("currencies", {})) == 29, f"Expected 29 currencies, got {len(pricing.get('currencies', {}))}"
    assert len(pricing.get("markets", {})) == 42, f"Expected 42 markets, got {len(pricing.get('markets', {}))}"
    assert len(idx_data.get("languages", {})) == 25, f"Expected 25 languages in index.json"

    # Verify zero-decimal precision rules
    for zc in ("JPY", "KRW", "VND", "CLP"):
        assert pricing["currencies"][zc]["decimals"] == 0 and pricing["currencies"][zc]["zero_decimal"] is True
    for code, cm in pricing["currencies"].items():
        if code not in ("JPY", "KRW", "VND", "CLP"):
            assert cm["decimals"] == 2 and cm["zero_decimal"] is False

    report_langs: Dict[str, dict] = {}
    all_missing = 0
    all_leaked_placeholders = 0

    for lg, lmeta in LANGUAGES_25.items():
        p = I18N_DIR / f"{lg}.json"
        assert p.exists(), f"Missing language pack: {p}"
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data.get("lang") == lg
        assert data.get("dir") == lmeta["dir"]
        assert data.get("native_name") == lmeta["native_name"]
        assert isinstance(data.get("ui"), dict) and len(data["ui"]) >= 50
        assert isinstance(data.get("patterns"), list) and len(data["patterns"]) >= 15
        smap: Dict[str, str] = data.get("strings") or {}

        missing = [s for s in html_strings if not smap.get(s)]
        leaked = [k for k, v in smap.items() if re.search(r"[\u27e6\u27e7]|Z\s*X\s*T\s*K\s*\d", v, re.I)]
        all_missing += len(missing)
        all_leaked_placeholders += len(leaked)

        if lg == "en":
            diff_pct = 100.0
            identical_nl = []
        else:
            identical_nl = [s for s in natural_html_strings if smap.get(s) == s]
            diff_count = len(natural_html_strings) - len(identical_nl)
            diff_pct = round(100.0 * diff_count / max(1, len(natural_html_strings)), 2)

        report_langs[lg] = {
            "file_kb": round(p.stat().st_size / 1024.0, 1),
            "dir": data["dir"],
            "total_strings": len(smap),
            "html_coverage_pct": round(100.0 * (len(html_strings) - len(missing)) / max(1, len(html_strings)), 2),
            "distinct_from_en_pct": diff_pct,
            "cognate_or_identical_count": len(identical_nl),
            "missing_count": len(missing),
            "leaked_placeholders": len(leaked),
        }

    summary = {
        "ok": all_missing == 0 and all_leaked_placeholders == 0,
        "html_files_count": len(per_file),
        "html_extracted_strings": len(html_strings),
        "html_natural_language_strings": len(natural_html_strings),
        "currencies_count": len(pricing["currencies"]),
        "markets_count": len(pricing["markets"]),
        "languages_count": len(report_langs),
        "total_missing_across_all_25_packs": all_missing,
        "total_leaked_placeholders": all_leaked_placeholders,
        "languages": report_langs,
    }
    LOG.info(
        "VERIFICATION PASSED=%s | HTML files=%d | HTML strings=%d (NL=%d) | Missing=%d | Leaked=%d",
        summary["ok"],
        summary["html_files_count"],
        summary["html_extracted_strings"],
        summary["html_natural_language_strings"],
        all_missing,
        all_leaked_placeholders,
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="TianxiaOS 42-Market & 25-Language Localization Compiler")
    parser.add_argument("--compile-pricing", action="store_true", help="Compile 29 currencies & 42 markets into pricing.json")
    parser.add_argument("--compile-i18n", action="store_true", help="Compile all 25 language packs into ui/i18n/*.json")
    parser.add_argument("--verify", action="store_true", help="Verify 100%% HTML coverage & schema invariants")
    parser.add_argument("--all", action="store_true", help="Run pricing compilation, i18n compilation, and verification")
    parser.add_argument("--workers", type=int, default=10, help="Concurrent persistent-TLS translation workers")
    parser.add_argument("--langs", type=str, default="", help="Optional comma-separated subset of languages to compile")
    args = parser.parse_args()

    run_all = args.all or not (args.compile_pricing or args.compile_i18n or args.verify)
    target_langs = [x.strip() for x in args.langs.split(",") if x.strip()] or None

    if run_all or args.compile_pricing:
        compile_pricing_json()
    if run_all or args.compile_i18n:
        compile_all_language_packs(max_workers=args.workers, target_langs=target_langs)
    if run_all or args.verify:
        summary = verify_all_packs()
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0 if summary["ok"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
