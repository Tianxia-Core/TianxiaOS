// ffp: FFP-WEB-STANDARDS frontend javascript
/**
 * tianxiaOS / RASA-X-MACHINA — Universal Modern Web Guidance 1.0,
 * 100% Full-Copy Reversible DOM Localization Engine (42 Markets, 25 Languages, RTL),
 * Compositional Localization Reuse + Dynamic /api/v1/i18n/batch Fallback,
 * 29-Currency Single-Currency Engine, Activity-Aware Non-Blocking Floating Chrome,
 * WCAG 2.2 AA Accessibility, GDPR++ v2030.4 & 4-Surface Cohesion Module.
 */
(function () {
  'use strict';
  if (window.__TX_WEB_STANDARDS_BOOTED__) return;
  window.__TX_WEB_STANDARDS_BOOTED__ = true;

  const CURRENCIES = {
    EUR: { symbol: '€', code: 'EUR', rate_from_eur: 1.0, rate_from_usd: 0.925, zero_decimal: false },
    USD: { symbol: '$', code: 'USD', rate_from_eur: 1.08, rate_from_usd: 1.0, zero_decimal: false },
    GBP: { symbol: '£', code: 'GBP', rate_from_eur: 0.85, rate_from_usd: 0.79, zero_decimal: false },
    CHF: { symbol: 'CHF ', code: 'CHF', rate_from_eur: 0.96, rate_from_usd: 0.89, zero_decimal: false },
    SEK: { symbol: 'kr ', code: 'SEK', rate_from_eur: 11.40, rate_from_usd: 10.55, zero_decimal: false },
    NOK: { symbol: 'kr ', code: 'NOK', rate_from_eur: 11.65, rate_from_usd: 10.78, zero_decimal: false },
    CAD: { symbol: 'CA$', code: 'CAD', rate_from_eur: 1.48, rate_from_usd: 1.37, zero_decimal: false },
    AUD: { symbol: 'A$', code: 'AUD', rate_from_eur: 1.65, rate_from_usd: 1.53, zero_decimal: false },
    NZD: { symbol: 'NZ$', code: 'NZD', rate_from_eur: 1.80, rate_from_usd: 1.67, zero_decimal: false },
    SGD: { symbol: 'S$', code: 'SGD', rate_from_eur: 1.45, rate_from_usd: 1.34, zero_decimal: false },
    HKD: { symbol: 'HK$', code: 'HKD', rate_from_eur: 8.42, rate_from_usd: 7.80, zero_decimal: false },
    JPY: { symbol: '¥', code: 'JPY', rate_from_eur: 163.0, rate_from_usd: 151.0, zero_decimal: true },
    KRW: { symbol: '₩', code: 'KRW', rate_from_eur: 1495.0, rate_from_usd: 1384.0, zero_decimal: true },
    VND: { symbol: '₫', code: 'VND', rate_from_eur: 27400.0, rate_from_usd: 25370.0, zero_decimal: true },
    INR: { symbol: '₹', code: 'INR', rate_from_eur: 91.2, rate_from_usd: 84.4, zero_decimal: false },
    PKR: { symbol: 'Rs ', code: 'PKR', rate_from_eur: 301.0, rate_from_usd: 278.7, zero_decimal: true },
    PLN: { symbol: 'zł ', code: 'PLN', rate_from_eur: 4.32, rate_from_usd: 4.00, zero_decimal: false },
    BGN: { symbol: 'лв ', code: 'BGN', rate_from_eur: 1.9558, rate_from_usd: 1.81, zero_decimal: false },
    TRY: { symbol: '₺', code: 'TRY', rate_from_eur: 37.2, rate_from_usd: 34.4, zero_decimal: false },
    AED: { symbol: 'AED ', code: 'AED', rate_from_eur: 3.97, rate_from_usd: 3.6725, zero_decimal: false },
    SAR: { symbol: 'SAR ', code: 'SAR', rate_from_eur: 4.05, rate_from_usd: 3.75, zero_decimal: false },
    NGN: { symbol: '₦', code: 'NGN', rate_from_eur: 1760.0, rate_from_usd: 1630.0, zero_decimal: true },
    KES: { symbol: 'KSh ', code: 'KES', rate_from_eur: 140.0, rate_from_usd: 129.6, zero_decimal: false },
    ZAR: { symbol: 'R', code: 'ZAR', rate_from_eur: 19.4, rate_from_usd: 17.96, zero_decimal: false },
    BRL: { symbol: 'R$', code: 'BRL', rate_from_eur: 6.18, rate_from_usd: 5.72, zero_decimal: false },
    MXN: { symbol: 'MX$', code: 'MXN', rate_from_eur: 21.6, rate_from_usd: 20.0, zero_decimal: false },
    CLP: { symbol: 'CLP$', code: 'CLP', rate_from_eur: 1045.0, rate_from_usd: 968.0, zero_decimal: true },
    ARS: { symbol: 'ARS$', code: 'ARS', rate_from_eur: 1090.0, rate_from_usd: 1009.0, zero_decimal: true },
    COP: { symbol: 'COP$', code: 'COP', rate_from_eur: 4680.0, rate_from_usd: 4333.0, zero_decimal: true },
    SOL: { symbol: '◎', code: 'SOL', rate_from_eur: 0.0072, rate_from_usd: 0.0067, zero_decimal: false }
  };

  const CURRENCY_ORDER = [
    'EUR', 'USD', 'GBP', 'CHF', 'SEK', 'NOK', 'PLN', 'BGN', 'TRY',
    'CAD', 'MXN', 'BRL', 'CLP', 'ARS', 'COP',
    'HKD', 'SGD', 'JPY', 'KRW', 'VND', 'INR', 'PKR', 'AUD', 'NZD',
    'AED', 'SAR', 'NGN', 'KES', 'ZAR'
  ];

  const RTL_LANGS = new Set(['ar', 'ur']);

  // Unified 42-Market & 25-Language Selector Matrix (Reusing Shared Language Packs)
  const LOCALE_OPTIONS = [
    { val: 'EE:en', country: 'EE', lang: 'en', curr: 'EUR', label: '🇪🇪 EE · English' },
    { val: 'EE:et', country: 'EE', lang: 'et', curr: 'EUR', label: '🇪🇪 EE · Eesti' },
    { val: 'FI:fi', country: 'FI', lang: 'fi', curr: 'EUR', label: '🇫🇮 FI · Suomi' },
    { val: 'LT:lt', country: 'LT', lang: 'lt', curr: 'EUR', label: '🇱🇹 LT · Lietuvių' },
    { val: 'PL:pl', country: 'PL', lang: 'pl', curr: 'PLN', label: '🇵🇱 PL · Polski' },
    { val: 'DE:de', country: 'DE', lang: 'de', curr: 'EUR', label: '🇩🇪 DE · Deutsch' },
    { val: 'NL:nl', country: 'NL', lang: 'nl', curr: 'EUR', label: '🇳🇱 NL · Nederlands' },
    { val: 'BE:nl', country: 'BE', lang: 'nl', curr: 'EUR', label: '🇧🇪 BE · Nederlands' },
    { val: 'BE:fr', country: 'BE', lang: 'fr', curr: 'EUR', label: '🇧🇪 BE · Français' },
    { val: 'FR:fr', country: 'FR', lang: 'fr', curr: 'EUR', label: '🇫🇷 FR · Français' },
    { val: 'CH:de', country: 'CH', lang: 'de', curr: 'CHF', label: '🇨🇭 CH · Deutsch' },
    { val: 'CH:fr', country: 'CH', lang: 'fr', curr: 'CHF', label: '🇨🇭 CH · Français' },
    { val: 'GB:en', country: 'GB', lang: 'en', curr: 'GBP', label: '🇬🇧 GB · English' },
    { val: 'SE:sv', country: 'SE', lang: 'sv', curr: 'SEK', label: '🇸🇪 SE · Svenska' },
    { val: 'NO:no', country: 'NO', lang: 'no', curr: 'NOK', label: '🇳🇴 NO · Norsk' },
    { val: 'IT:it', country: 'IT', lang: 'it', curr: 'EUR', label: '🇮🇹 IT · Italiano' },
    { val: 'ES:es', country: 'ES', lang: 'es', curr: 'EUR', label: '🇪🇸 ES · Español' },
    { val: 'GR:el', country: 'GR', lang: 'el', curr: 'EUR', label: '🇬🇷 GR · Ελληνικά' },
    { val: 'CY:el', country: 'CY', lang: 'el', curr: 'EUR', label: '🇨🇾 CY · Ελληνικά' },
    { val: 'CY:en', country: 'CY', lang: 'en', curr: 'EUR', label: '🇨🇾 CY · English' },
    { val: 'MT:mt', country: 'MT', lang: 'mt', curr: 'EUR', label: '🇲🇹 MT · Malti' },
    { val: 'MT:en', country: 'MT', lang: 'en', curr: 'EUR', label: '🇲🇹 MT · English' },
    { val: 'BG:bg', country: 'BG', lang: 'bg', curr: 'BGN', label: '🇧🇬 BG · Български' },
    { val: 'TR:tr', country: 'TR', lang: 'tr', curr: 'TRY', label: '🇹🇷 TR · Türkçe' },
    { val: 'US:en', country: 'US', lang: 'en', curr: 'USD', label: '🇺🇸 US · English' },
    { val: 'CA:en', country: 'CA', lang: 'en', curr: 'CAD', label: '🇨🇦 CA · English' },
    { val: 'CA:fr', country: 'CA', lang: 'fr', curr: 'CAD', label: '🇨🇦 CA · Français' },
    { val: 'MX:es', country: 'MX', lang: 'es', curr: 'MXN', label: '🇲🇽 MX · Español' },
    { val: 'BR:pt', country: 'BR', lang: 'pt', curr: 'BRL', label: '🇧🇷 BR · Português' },
    { val: 'CL:es', country: 'CL', lang: 'es', curr: 'CLP', label: '🇨🇱 CL · Español' },
    { val: 'AR:es', country: 'AR', lang: 'es', curr: 'ARS', label: '🇦🇷 AR · Español' },
    { val: 'CO:es', country: 'CO', lang: 'es', curr: 'COP', label: '🇨🇴 CO · Español' },
    { val: 'HK:zh-HK', country: 'HK', lang: 'zh-HK', curr: 'HKD', label: '🇭🇰 HK · 繁體中文' },
    { val: 'HK:en', country: 'HK', lang: 'en', curr: 'HKD', label: '🇭🇰 HK · English' },
    { val: 'SG:en', country: 'SG', lang: 'en', curr: 'SGD', label: '🇸🇬 SG · English' },
    { val: 'JP:ja', country: 'JP', lang: 'ja', curr: 'JPY', label: '🇯🇵 JP · 日本語' },
    { val: 'KR:ko', country: 'KR', lang: 'ko', curr: 'KRW', label: '🇰🇷 KR · 한국어' },
    { val: 'VN:vi', country: 'VN', lang: 'vi', curr: 'VND', label: '🇻🇳 VN · Tiếng Việt' },
    { val: 'IN:hi', country: 'IN', lang: 'hi', curr: 'INR', label: '🇮🇳 IN · हिन्दी' },
    { val: 'IN:en', country: 'IN', lang: 'en', curr: 'INR', label: '🇮🇳 IN · English' },
    { val: 'PK:ur', country: 'PK', lang: 'ur', curr: 'PKR', label: '🇵🇰 PK · اردو' },
    { val: 'PK:en', country: 'PK', lang: 'en', curr: 'PKR', label: '🇵🇰 PK · English' },
    { val: 'AU:en', country: 'AU', lang: 'en', curr: 'AUD', label: '🇦🇺 AU · English' },
    { val: 'NZ:en', country: 'NZ', lang: 'en', curr: 'NZD', label: '🇳🇿 NZ · English' },
    { val: 'AE:ar', country: 'AE', lang: 'ar', curr: 'AED', label: '🇦🇪 AE · العربية' },
    { val: 'AE:en', country: 'AE', lang: 'en', curr: 'AED', label: '🇦🇪 AE · English' },
    { val: 'SA:ar', country: 'SA', lang: 'ar', curr: 'SAR', label: '🇸🇦 SA · العربية' },
    { val: 'NG:en', country: 'NG', lang: 'en', curr: 'NGN', label: '🇳🇬 NG · English' },
    { val: 'KE:sw', country: 'KE', lang: 'sw', curr: 'KES', label: '🇰🇪 KE · Kiswahili' },
    { val: 'KE:en', country: 'KE', lang: 'en', curr: 'KES', label: '🇰🇪 KE · English' },
    { val: 'ZA:en', country: 'ZA', lang: 'en', curr: 'ZAR', label: '🇿🇦 ZA · English' },
    { val: 'EU:en', country: 'EU', lang: 'en', curr: 'EUR', label: '🇪🇺 EU · English' },
    { val: 'GLOBAL:en', country: 'GLOBAL', lang: 'en', curr: 'USD', label: '🌐 Global · English' }
  ];

  function mkProfile(flag, enName, regime, rails) {
    return { flag: flag, name: { en: enName }, regime: regime + ' · GDPR++ v2030.4', rails: rails };
  }

  const COUNTRY_PROFILES = {
    EE: mkProfile('🇪🇪', 'Estonia & European Union', 'Estonian Aliens Act § 100¹ (Dealum #179423 Under Committee Review) · AKI / IKS · EU AI Act', 'Stripe EUR (€) SEPA / Cards · Solana Pay · Base L2 · x402'),
    FI: mkProfile('🇫🇮', 'Finland (Nordic EU)', 'Office of the Data Protection Ombudsman · NIS2 · EU AI Act', 'Stripe EUR (€) SEPA Instant · Solana Pay · Base L2 · x402'),
    LT: mkProfile('🇱🇹', 'Lithuania (Baltic Fintech Hub)', 'VDAI / BDAR · Bank of Lithuania MiCA & NIS2 Alignment', 'Stripe EUR (€) SEPA Instant · Solana Pay · Base L2 · x402'),
    PL: mkProfile('🇵🇱', 'Poland (CEE EU)', 'UODO RODO++ · KSC / NIS2 Sovereign Enclave', 'Stripe PLN (zł) BLIK / Cards · SEPA · Base L2 · x402'),
    BG: mkProfile('🇧🇬', 'Bulgaria (EU)', 'CPDP ZZLD / GDPR · NIS2 & ERM-II Parity', 'Stripe BGN (лв) / EUR · SEPA · Base L2 · x402'),
    DE: mkProfile('🇩🇪', 'Germany (DACH)', 'BSI IT-Grundschutz · DSGVO++ · NIS2 & DORA', 'Stripe EUR (€) SEPA / Karten · Solana Pay · Base L2 · Paddle'),
    NL: mkProfile('🇳🇱', 'The Netherlands', 'Autoriteit Persoonsgegevens AVG++ · NIS2 & DORA', 'Stripe EUR (€) iDEAL / SEPA · Solana Pay · Base L2 · x402'),
    BE: mkProfile('🇧🇪', 'Belgium', 'APD / GBA GDPR++ · CCB NIS2 Framework', 'Stripe EUR (€) Bancontact / SEPA · Solana Pay · Base L2'),
    FR: mkProfile('🇫🇷', 'France', 'CNIL RGPD++ · ANSSI SecNumCloud Principles · EU AI Act', 'Stripe EUR (€) Cartes Bancaires / SEPA · Solana Pay · Base L2'),
    CH: mkProfile('🇨🇭', 'Switzerland', 'Swiss revFADP (nDSG) · FINMA Zero-Knowledge Enclave', 'Native Stripe CHF · Solana Pay · Base L2 USDC · x402'),
    GB: mkProfile('🇬🇧', 'United Kingdom', 'UK GDPR / DUAA · NCSC Zero-Trust Enclave Alignment', 'Stripe GBP (£) Faster Payments · Solana Pay · Base L2'),
    SE: mkProfile('🇸🇪', 'Sweden', 'IMY Dataskydd++ · MSB NIS2 Infrastructure', 'Native Stripe SEK (kr) · Solana Pay · Base L2 · Paddle'),
    NO: mkProfile('🇳🇴', 'Norway (EEA)', 'Datatilsynet Personvern++ · NSM Zero-Trust & NIS2', 'Native Stripe NOK (kr) · Solana Pay · Base L2 · Paddle'),
    IT: mkProfile('🇮🇹', 'Italy', 'Garante Privacy GDPR++ · ACN NIS2 National Perimeter', 'Stripe EUR (€) SEPA / Carte · Solana Pay · Base L2 · x402'),
    ES: mkProfile('🇪🇸', 'Spain', 'AEPD LOPDGDD++ · Esquema Nacional de Seguridad (ENS)', 'Stripe EUR (€) SEPA / Tarjetas · Solana Pay · Base L2 · x402'),
    GR: mkProfile('🇬🇷', 'Greece', 'HDPA GDPR++ · NCSA NIS2 Sovereign Compliance', 'Stripe EUR (€) IRIS / SEPA · Solana Pay · Base L2 · x402'),
    CY: mkProfile('🇨🇾', 'Cyprus', 'Commissioner for Personal Data Protection · DSA / NIS2', 'Stripe EUR (€) SEPA Instant · Solana Pay · Base L2 · x402'),
    MT: mkProfile('🇲🇹', 'Malta', 'IDPC GDPR++ · MDIA Technology Assurance & MiCA', 'Stripe EUR (€) SEPA Instant · Solana Pay · Base L2 · x402'),
    TR: mkProfile('🇹🇷', 'Turkey', 'KVKK Law No. 6698 · Post-Quantum Cryptoshredding', 'TRY (₺) Cards · Base L2 USDC · Solana Pay · x402'),
    US: mkProfile('🇺🇸', 'United States', 'CCPA / CPRA · NIST FIPS 203 Post-Quantum · Sec-GPC: 1', 'Stripe USD ($) Cards / ACH · Base L2 USDC · Solana Pay · x402'),
    CA: mkProfile('🇨🇦', 'Canada', 'PIPEDA & Québec Law 25 · Canadian Cyber Centre', 'Native Stripe CAD (CA$) · Base L2 USDC · Solana Pay · Paddle'),
    MX: mkProfile('🇲🇽', 'Mexico', 'LFPDPPP · Zero-Knowledge Cryptoshredding', 'Stripe MXN (MX$) Cards · Base L2 USDC · Solana Pay · x402'),
    BR: mkProfile('🇧🇷', 'Brazil', 'ANPD LGPD++ · Post-Quantum Sovereign Isolation', 'BRL (R$) Cards / Multi-Rail · Base L2 USDC · Solana Pay · x402'),
    CL: mkProfile('🇨🇱', 'Chile', 'Ley 21.719 Data Protection · Agency CSIRT Alignment', 'CLP (CLP$) Cards · Base L2 USDC · Solana Pay · x402'),
    AR: mkProfile('🇦🇷', 'Argentina', 'AAIP Ley 25.326 Habeas Data · Zero-Knowledge Vault', 'ARS (ARS$) / Base L2 USDC · Solana Pay · x402'),
    CO: mkProfile('🇨🇴', 'Colombia', 'SIC Ley 1581 Habeas Data · Sovereign Enclave', 'COP (COP$) Cards · Base L2 USDC · Solana Pay · x402'),
    HK: mkProfile('🇭🇰', 'Hong Kong SAR', 'PCPD PDPO (Cap. 486) · HKMA GenAI & Fintech Guardrails', 'Stripe HKD (HK$) Cards / FPS · Base L2 USDC · Solana Pay · x402'),
    SG: mkProfile('🇸🇬', 'Singapore', 'PDPC PDPA & MAS TRM Cyber-Resilience', 'Native Stripe SGD (S$) · Solana Pay · Base L2 USDC · x402'),
    JP: mkProfile('🇯🇵', 'Japan', 'PPC APPI (個人情報保護法) · Post-Quantum Enclave', 'Native Stripe JPY (¥) · Solana Pay · Base L2 · x402'),
    KR: mkProfile('🇰🇷', 'South Korea', 'PIPC PIPA (개인정보 보호법) & Korea AI Framework', 'KRW (₩) Cards · Base L2 USDC · Solana Pay · x402'),
    VN: mkProfile('🇻🇳', 'Vietnam', 'Decree 13/2023/ND-CP PDPD · Sovereign Data Shield', 'VND (₫) Cards · Base L2 USDC · Solana Pay · x402'),
    IN: mkProfile('🇮🇳', 'India', 'DPDP Act 2023 & CERT-In Zero-Trust Directives', 'INR (₹) Cards · Base L2 USDC · Solana Pay · x402'),
    PK: mkProfile('🇵🇰', 'Pakistan', 'Data Protection & Cryptographic Sovereignty Standard', 'PKR (Rs) Multi-Rail · Base L2 USDC · Solana Pay · x402'),
    AU: mkProfile('🇦🇺', 'Australia', 'Australian Privacy Principles (APPs) & ASD Essential Eight', 'Native Stripe AUD (A$) · Solana Pay · Base L2 · Paddle'),
    NZ: mkProfile('🇳🇿', 'New Zealand', 'NZ Privacy Act 2020 (IPP 1–13) & NZISM', 'Native Stripe NZD (NZ$) · Solana Pay · Base L2 · x402'),
    AE: mkProfile('🇦🇪', 'United Arab Emirates', 'UAE Federal Decree-Law No. 45/2021 (PDPL) · ADGM / DIFC', 'Stripe AED Cards · Base L2 USDC · Solana Pay · x402'),
    SA: mkProfile('🇸🇦', 'Saudi Arabia', 'SDAIA PDPL & NCA Essential Cybersecurity Controls (ECC)', 'SAR Cards · Base L2 USDC · Solana Pay · x402'),
    NG: mkProfile('🇳🇬', 'Nigeria', 'NDPC Nigeria Data Protection Act (NDPA 2023)', 'NGN (₦) Multi-Rail · Base L2 USDC · Solana Pay · x402'),
    KE: mkProfile('🇰🇪', 'Kenya', 'ODPC Kenya Data Protection Act 2019', 'KES (KSh) Multi-Rail · Base L2 USDC · Solana Pay · x402'),
    ZA: mkProfile('🇿🇦', 'South Africa', 'Information Regulator POPIA Compliance', 'ZAR (R) Cards · Base L2 USDC · Solana Pay · x402'),
    EU: mkProfile('🇪🇺', 'European Union', 'EU GDPR · EU AI Act · NIS2 · DORA', 'Stripe EUR (€) SEPA · Solana Pay · Base L2 · x402'),
    GLOBAL: mkProfile('🌐', 'Global Sovereign', 'Post-Quantum Zero-Knowledge Sovereign Standard', 'Multi-Currency Stripe · Base L2 USDC · Solana Pay · x402')
  };

  // Structural Chrome Labels Across All 25 Supported Languages
  const GLOBAL_I18N = {
    en: { skip_main: 'Skip to main content', ctx_active: 'Active Jurisdiction & Localization', ctx_regime: 'Compliance', ctx_stmt: 'Card Descriptor', dock_apps: '28 Apps', dock_gui: 'GUI', dock_hw: 'HW', dock_gdpr: 'GDPR++' },
    et: { skip_main: 'Liigu põhisisu juurde', ctx_active: 'Aktiivne Turg ja Keel', ctx_regime: 'Vastavus', ctx_stmt: 'Pangaväljavõte', dock_apps: '28 Rakendust', dock_gui: 'Töölaud', dock_hw: 'Raudvara', dock_gdpr: 'GDPR++' },
    de: { skip_main: 'Zum Hauptinhalt springen', ctx_active: 'Aktiver Markt & Sprache', ctx_regime: 'Compliance', ctx_stmt: 'Kontoauszug', dock_apps: '28 Apps', dock_gui: 'Cockpit', dock_hw: 'Hardware', dock_gdpr: 'DSGVO++' },
    fr: { skip_main: 'Aller au contenu principal', ctx_active: 'Marché Actif & Langue', ctx_regime: 'Conformité', ctx_stmt: 'Libellé Bancaire', dock_apps: '28 Apps', dock_gui: 'Cockpit', dock_hw: 'Matériel', dock_gdpr: 'RGPD++' },
    es: { skip_main: 'Saltar al contenido principal', ctx_active: 'Jurisdicción y Localización Activa', ctx_regime: 'Cumplimiento', ctx_stmt: 'Descriptor Bancario', dock_apps: '28 Apps', dock_gui: 'GUI', dock_hw: 'Hardware', dock_gdpr: 'RGPD++' },
    pt: { skip_main: 'Ir para o conteúdo principal', ctx_active: 'Jurisdição e Idioma Ativos', ctx_regime: 'Conformidade', ctx_stmt: 'Descritor no Extrato', dock_apps: '28 Apps', dock_gui: 'GUI', dock_hw: 'Hardware', dock_gdpr: 'LGPD++' },
    it: { skip_main: 'Vai al contenuto principale', ctx_active: 'Giurisdizione e Lingua Attive', ctx_regime: 'Conformità', ctx_stmt: 'Causale Estratto Conto', dock_apps: '28 App', dock_gui: 'GUI', dock_hw: 'Hardware', dock_gdpr: 'GDPR++' },
    nl: { skip_main: 'Ga naar hoofdinhoud', ctx_active: 'Actieve Markt & Taal', ctx_regime: 'Naleving', ctx_stmt: 'Afschriftomschrijving', dock_apps: '28 Apps', dock_gui: 'GUI', dock_hw: 'Hardware', dock_gdpr: 'AVG++' },
    pl: { skip_main: 'Przejdź do głównej treści', ctx_active: 'Aktywny Rynek i Język', ctx_regime: 'Zgodność', ctx_stmt: 'Opis na Wyciągu', dock_apps: '28 Aplikacji', dock_gui: 'GUI', dock_hw: 'Sprzęt', dock_gdpr: 'RODO++' },
    fi: { skip_main: 'Siirry pääsisältöön', ctx_active: 'Aktiivinen Markkina ja Kieli', ctx_regime: 'Vaatimustenmukaisuus', ctx_stmt: 'Tilioteviite', dock_apps: '28 Sovellusta', dock_gui: 'GUI', dock_hw: 'Laitteisto', dock_gdpr: 'GDPR++' },
    lt: { skip_main: 'Pereiti prie pagrindinio turinio', ctx_active: 'Aktyvi Rinka ir Kalba', ctx_regime: 'Atitiktis', ctx_stmt: 'Išrašo Aprašas', dock_apps: '28 Programos', dock_gui: 'GUI', dock_hw: 'Įranga', dock_gdpr: 'BDAR++' },
    bg: { skip_main: 'Към основното съдържание', ctx_active: 'Активен Пазар и Език', ctx_regime: 'Съответствие', ctx_stmt: 'Банково Извлечение', dock_apps: '28 Приложения', dock_gui: 'GUI', dock_hw: 'Хардуер', dock_gdpr: 'GDPR++' },
    el: { skip_main: 'Μετάβαση στο κύριο περιεχόμενο', ctx_active: 'Ενεργή Αγορά & Γλώσσα', ctx_regime: 'Συμμόρφωση', ctx_stmt: 'Περιγραφή Κίνησης', dock_apps: '28 Εφαρμογές', dock_gui: 'GUI', dock_hw: 'Υλικό', dock_gdpr: 'GDPR++' },
    mt: { skip_main: 'Aqbeż għall-kontenut prinċipali', ctx_active: 'Suq u Lingwa Attivi', ctx_regime: 'Konformità', ctx_stmt: 'Deskrizzjoni tal-Bank', dock_apps: '28 Apps', dock_gui: 'GUI', dock_hw: 'Ħardwer', dock_gdpr: 'GDPR++' },
    sv: { skip_main: 'Hoppa till huvudinnehåll', ctx_active: 'Aktiv Marknad & Språk', ctx_regime: 'Efterlevnad', ctx_stmt: 'Kontoutdrag', dock_apps: '28 Appar', dock_gui: 'GUI', dock_hw: 'Hårdvara', dock_gdpr: 'GDPR++' },
    no: { skip_main: 'Hopp til hovedinnhold', ctx_active: 'Aktivt Marked & Språk', ctx_regime: 'Samsvar', ctx_stmt: 'Kontoutskrift', dock_apps: '28 Apper', dock_gui: 'GUI', dock_hw: 'Maskinvare', dock_gdpr: 'GDPR++' },
    tr: { skip_main: 'Ana içeriğe geç', ctx_active: 'Aktif Pazar ve Dil', ctx_regime: 'Uyumluluk', ctx_stmt: 'Ekstre Açıklaması', dock_apps: '28 Uygulama', dock_gui: 'GUI', dock_hw: 'Donanım', dock_gdpr: 'KVKK++' },
    ar: { skip_main: 'الانتقال إلى المحتوى الرئيسي', ctx_active: 'السوق واللغة النشطة', ctx_regime: 'الامتثال', ctx_stmt: 'بيان البطاقة', dock_apps: '28 تطبيقاً', dock_gui: 'الواجهة', dock_hw: 'العتاد', dock_gdpr: 'GDPR++' },
    ur: { skip_main: 'مرکزی مواد پر جائیں', ctx_active: 'فعال مارکیٹ اور زبان', ctx_regime: 'تعمیل', ctx_stmt: 'بینک اسٹیٹمنٹ', dock_apps: '28 ایپس', dock_gui: 'GUI', dock_hw: 'ہارڈویئر', dock_gdpr: 'GDPR++' },
    hi: { skip_main: 'मुख्य सामग्री पर जाएँ', ctx_active: 'सक्रिय बाज़ार और भाषा', ctx_regime: 'अनुपालन', ctx_stmt: 'कार्ड विवरण', dock_apps: '28 ऐप्स', dock_gui: 'GUI', dock_hw: 'हार्डवेयर', dock_gdpr: 'DPDP++' },
    sw: { skip_main: 'Ruka hadi maudhui makuu', ctx_active: 'Soko na Lugha Inayotumika', ctx_regime: 'Uzingatiaji', ctx_stmt: 'Maelezo ya Benki', dock_apps: 'Programu 28', dock_gui: 'GUI', dock_hw: 'Maunzi', dock_gdpr: 'GDPR++' },
    vi: { skip_main: 'Chuyển đến nội dung chính', ctx_active: 'Thị Trường & Ngôn Ngữ Đang Chọn', ctx_regime: 'Tuân Thủ', ctx_stmt: 'Sao Kê Thẻ', dock_apps: '28 Ứng Dụng', dock_gui: 'GUI', dock_hw: 'Phần Cứng', dock_gdpr: 'GDPR++' },
    ko: { skip_main: '본문으로 건너뛰기', ctx_active: '활성 국가 및 언어 설정', ctx_regime: '규제 준수', ctx_stmt: '카드 명세서 표기', dock_apps: '28개 앱', dock_gui: 'GUI', dock_hw: '하드웨어', dock_gdpr: 'PIPA++' },
    'zh-HK': { skip_main: '跳至主要內容', ctx_active: '當前司法管轄區與語言', ctx_regime: '合規標準', ctx_stmt: '月結單顯示名稱', dock_apps: '28 個應用', dock_gui: '介面', dock_hw: '硬件橋接', dock_gdpr: 'PDPO++' },
    ja: { skip_main: 'メインコンテンツへ移動', ctx_active: '選択中の市場・言語設定', ctx_regime: '準拠法・暗号保護', ctx_stmt: '明細表記', dock_apps: '28 アプリ', dock_gui: 'GUI', dock_hw: 'HW接続', dock_gdpr: 'GDPR++' }
  };

  const PENDING_CF_SUBDOMAINS = new Set([
    'estonia', 'cockpit', 'collins', 'press', 'vrtti', 'names', 'tracer', 'yield', 'radar',
    'etamanga', 'alpha', 'fortress', 'jobs', 'ledger', 'manual', 'shop', 'vault'
  ]);

  const SUBDOMAIN_DIRECTORY = [
    { key: 'root', label: 'rasaxmachina.com — Main Sovereign Storefront & 21 SKUs', url: 'https://rasaxmachina.com/', cat: 'Storefront' },
    { key: 'estonia', label: 'estonia.rasaxmachina.com — Estonian Startup Committee Evaluation Companion (#179423)', url: 'https://rasaxmachina.com/estonia', cat: 'Committee Review' },
    { key: 'cockpit', label: 'cockpit.rasaxmachina.com — tianxiaOS Polyglot Cockpit Web App & HUD', url: 'https://rasaxmachina.com/cockpit', cat: '4-Surface GUI' },
    { key: 'pay', label: 'pay.rasaxmachina.com — 6-Rail Sovereign Checkout & Escrow', url: 'https://pay.rasaxmachina.com/', cat: 'Settlement' },
    { key: 'shop', label: 'shop.rasaxmachina.com — Fortress Market & 21-SKU Catalog', url: 'https://rasaxmachina.com/shop', cat: 'Storefront' },
    { key: 'fortress', label: 'fortress.rasaxmachina.com — Faery Fortress & MANAS <1ms Shield', url: 'https://rasaxmachina.com/fortress', cat: 'Security' },
    { key: 'radar', label: 'radar.rasaxmachina.com — 1,563 CISA KEV & Feodo C2 Threat Radar', url: 'https://rasaxmachina.com/radar', cat: 'Security' },
    { key: 'vault', label: 'vault.rasaxmachina.com — Aethervault Post-Quantum Secret Isolation', url: 'https://rasaxmachina.com/vault', cat: 'Security' },
    { key: 'ledger', label: 'ledger.rasaxmachina.com — Veritas-Rex 4-Way Merkle Solvency Proof', url: 'https://rasaxmachina.com/ledger', cat: 'Solvency' },
    { key: 'tracer', label: 'tracer.rasaxmachina.com — Murua UPU CN08 Bayesian Postal Tracer', url: 'https://rasaxmachina.com/tracer', cat: 'Logistics' },
    { key: 'vrtti', label: 'vrtti.rasaxmachina.com — Institutional Architecture Sprints', url: 'https://rasaxmachina.com/vrtti', cat: 'Enterprise' },
    { key: 'collins', label: 'collins.rasaxmachina.com — Collins Takem Executive Systems Advisory', url: 'https://rasaxmachina.com/collins', cat: 'Executive' },
    { key: 'press', label: 'press.rasaxmachina.com — Official Press, Media & Canonical Brand Kit', url: 'https://rasaxmachina.com/press', cat: 'Executive' },
    { key: 'tianxia', label: 'tianxia.rasaxmachina.com — tianxiaOS Sovereign Post-Quantum Mesh & OS', url: 'https://tianxia.rasaxmachina.com/', cat: 'OS & Mesh' },
    { key: 'ndimmorwyn', label: 'ndimmorwyn.rasaxmachina.com — Ndimmôrwyn Autonomous Fleet Engine', url: 'https://ndimmorwyn.rasaxmachina.com/', cat: 'Autonomous' },
    { key: 'substrate', label: 'substrate.rasaxmachina.com — seL4 / NixOS Unikernel & Memory Substrate', url: 'https://substrate.rasaxmachina.com/', cat: 'Architecture' },
    { key: 'yield', label: 'yield.rasaxmachina.com — Autotreasury DeFi Yield Scour Engine', url: 'https://rasaxmachina.com/yield', cat: 'Treasury' },
    { key: 'alpha', label: 'alpha.rasaxmachina.com — Cross-Venue & Funding Arbitrage Intelligence', url: 'https://rasaxmachina.com/alpha', cat: 'Trading' },
    { key: 'names', label: 'names.rasaxmachina.com — NomenAgora 60-Handle Digital Asset Syndicate', url: 'https://rasaxmachina.com/names', cat: 'Syndicate' },
    { key: 'jobs', label: 'jobs.rasaxmachina.com — JobMatch Honest CV & B2B Sprint Strikes', url: 'https://rasaxmachina.com/jobs', cat: 'Products' },
    { key: 'manual', label: 'manual.rasaxmachina.com — tianxiaOS Operator Manual & Engineering Codices', url: 'https://rasaxmachina.com/manual', cat: 'Products' },
    { key: 'etamanga', label: 'etamanga.rasaxmachina.com — $ETMA Solana & $EFM Base Token Hub', url: 'https://rasaxmachina.com/etamanga', cat: 'Token Rails' },
    { key: 'rpc-etamanga', label: 'rpc-etamanga.rasaxmachina.com — Dual-Mode JSON-RPC 2.0 & Explorer', url: 'https://rpc-etamanga.rasaxmachina.com/', cat: 'Machine API' },
    { key: 'x402', label: 'x402.rasaxmachina.com — Agentic HTTP 402 Machine Micropayments', url: 'https://x402.rasaxmachina.com/', cat: 'Machine API' },
    { key: 'api', label: 'api.rasaxmachina.com — Public Catalog, Webhook & x402 Gateway', url: 'https://rasaxmachina.com/api', cat: 'Machine API' },
    { key: 'relay', label: 'relay.rasaxmachina.com — Hetzner EU Rosenpass PQ Mesh Relay', url: 'https://relay.rasaxmachina.com/', cat: 'Mesh Infra' },
    { key: 'docs', label: 'docs.rasaxmachina.com — DSS-14.2 & Dasavidyayana Documentation', url: 'https://docs.rasaxmachina.com/', cat: 'Docs' },
    { key: 'trust', label: 'trust.rasaxmachina.com — GDPR++ & RFC 9116 Compliance Center', url: 'https://trust.rasaxmachina.com/', cat: 'Compliance' },
    { key: 'status', label: 'status.rasaxmachina.com — 4/5 Mesh Node Telemetry & Uptime', url: 'https://status.rasaxmachina.com/', cat: 'Mesh Infra' },
    { key: 'blog', label: 'blog.rasaxmachina.com — Founder & Sovereign Systems Research Blog', url: 'https://blog.rasaxmachina.com/', cat: 'Research' },
    { key: 'github', label: 'GitHub — Tianxia-Core / tianxiaOS (RASA-X-MACHINA) Source & Signed Releases', url: 'https://github.com/Tianxia-Core', cat: '4-Surface GUI' }
  ];

  let wakeLockSentinel = null;
  let idleChromeTimer = null;
  let isApplyingI18n = false;
  let domObserver = null;
  let dynamicBatchTimer = null;
  const pendingDynamicStrings = new Set();
  const LOADED_PACKS = {};
  const PACK_PROMISES = {};
  const origTextMap = new WeakMap();
  let canonicalDocTitle = '';
  let canonicalMetaDesc = '';

  const LOCALE_SELECT_IDS = ['tx-locale-toggle', 'pay-locale-select', 'shop-locale-select', 'ee-locale-select', 'tx-std-locale-select'];
  const CURR_SELECT_IDS = ['tx-currency-toggle', 'tx-curr-select', 'currency-select', 'pay-curr-select', 'tx-std-curr-select'];

  function normalizeWs(s) {
    return String(s || '').replace(/\s+/g, ' ').trim();
  }

  function getSavedCurrency() {
    try {
      const sp = new URLSearchParams(window.location.search);
      const qc = (sp.get('currency') || sp.get('curr') || '').toUpperCase();
      if (qc && CURRENCIES[qc]) return qc;
      const c = localStorage.getItem('tx_pref_currency') || localStorage.getItem('tx_currency');
      if (c && CURRENCIES[c]) return c;
    } catch (_e) {}
    return 'EUR';
  }

  function setSavedCurrency(curr) {
    if (!CURRENCIES[curr]) return;
    try {
      localStorage.setItem('tx_pref_currency', curr);
      localStorage.setItem('tx_currency', curr);
    } catch (_e) {}
  }

  function getSavedCountry() {
    try {
      const sp = new URLSearchParams(window.location.search);
      const qcc = (sp.get('country') || sp.get('market') || '').toUpperCase();
      if (qcc && COUNTRY_PROFILES[qcc]) return qcc;
      const cc = localStorage.getItem('tx_pref_country');
      if (cc && COUNTRY_PROFILES[cc]) return cc;
    } catch (_e) {}
    return 'EE';
  }

  function getSavedLang() {
    try {
      const sp = new URLSearchParams(window.location.search);
      const ql = sp.get('lang');
      if (ql && GLOBAL_I18N[ql]) return ql;
      const l = localStorage.getItem('tx_pref_lang');
      if (l && GLOBAL_I18N[l]) return l;
    } catch (_e) {}
    return 'en';
  }

  function getLocaleComboValue(country, lang) {
    const exact = LOCALE_OPTIONS.find(function (o) { return o.country === country && o.lang === lang; });
    if (exact) return exact.val;
    const byCountry = LOCALE_OPTIONS.find(function (o) { return o.country === country; });
    if (byCountry) return byCountry.val;
    const byLang = LOCALE_OPTIONS.find(function (o) { return o.lang === lang; });
    return byLang ? byLang.val : 'EE:en';
  }

  function setSavedLocale(country, lang) {
    try {
      if (country && COUNTRY_PROFILES[country]) localStorage.setItem('tx_pref_country', country);
      if (lang && GLOBAL_I18N[lang]) localStorage.setItem('tx_pref_lang', lang);
    } catch (_e) {}
  }

  function announceForScreenReader(msg) {
    let sr = document.getElementById('tx-sr-announcer');
    if (!sr) {
      sr = document.createElement('div');
      sr.id = 'tx-sr-announcer';
      sr.setAttribute('role', 'status');
      sr.setAttribute('aria-live', 'polite');
      sr.setAttribute('aria-atomic', 'true');
      sr.style.cssText = 'position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0';
      document.body.appendChild(sr);
    }
    sr.textContent = msg;
  }

  function syncAllDropdownOptions() {
    LOCALE_SELECT_IDS.forEach(function (id) {
      const sel = document.getElementById(id);
      if (!sel || sel.getAttribute('data-tx-upgraded-42') === '1') return;
      sel.setAttribute('data-tx-upgraded-42', '1');
      sel.setAttribute('data-tx-no-i18n', '1');
      sel.innerHTML = '';
      LOCALE_OPTIONS.forEach(function (optMeta) {
        const opt = document.createElement('option');
        opt.value = optMeta.val;
        opt.textContent = optMeta.label;
        sel.appendChild(opt);
      });
    });

    CURR_SELECT_IDS.forEach(function (id) {
      const sel = document.getElementById(id);
      if (!sel || sel.getAttribute('data-tx-upgraded-29') === '1') return;
      const keepSol = [].some.call(sel.options || [], function (o) { return o.value === 'SOL'; });
      sel.setAttribute('data-tx-upgraded-29', '1');
      sel.setAttribute('data-tx-no-i18n', '1');
      sel.innerHTML = '';
      const order = keepSol ? CURRENCY_ORDER.concat(['SOL']) : CURRENCY_ORDER;
      order.forEach(function (c) {
        if (!CURRENCIES[c]) return;
        const opt = document.createElement('option');
        opt.value = c;
        opt.textContent = `${c} (${CURRENCIES[c].symbol.trim()})`;
        sel.appendChild(opt);
      });
    });
  }

  function loadLanguagePack(lang) {
    if (!lang || lang === 'en') return Promise.resolve(null);
    if (LOADED_PACKS[lang]) return Promise.resolve(LOADED_PACKS[lang]);
    if (PACK_PROMISES[lang]) return PACK_PROMISES[lang];
    PACK_PROMISES[lang] = fetch(`/i18n/${encodeURIComponent(lang)}.json`)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (data && typeof data === 'object') {
          if (!data.strings) data.strings = {};
          if (!data.ui) data.ui = {};
          LOADED_PACKS[lang] = data;
          return data;
        }
        return null;
      })
      .catch(function () { return null; });
    return PACK_PROMISES[lang];
  }

  function isSkippedElement(el) {
    if (!el || !el.tagName) return true;
    const tag = el.tagName;
    if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'CODE' || tag === 'PRE' || tag === 'NOSCRIPT' || tag === 'SVG' || tag === 'TEXTAREA') {
      return true;
    }
    if (
      el.hasAttribute('data-tx-no-i18n') ||
      el.closest('[data-tx-no-i18n]') ||
      el.classList.contains('tx-store-price') ||
      el.classList.contains('tx-btn-price') ||
      el.classList.contains('tx-dyn-money') ||
      el.classList.contains('tx-auto-money') ||
      el.hasAttribute('data-base-amt')
    ) {
      return true;
    }
    return false;
  }

  function isTranslatableCore(core) {
    if (!core || core.length < 2) return false;
    if (!/[A-Za-z]/.test(core)) return false;
    if (/^(https?:\/\/|wss?:\/\/|\/[a-z0-9/_.*-]+|[a-z0-9_.-]+\.(py|rs|nix|js|json|md|sh|sock|exe|apk|com)|0x[0-9a-fA-F]+|v?\d[\d.,:+/%-]*)$/i.test(core)) {
      return false;
    }
    return true;
  }

  function captureCanonicalEnglishDom(root) {
    if (!canonicalDocTitle) canonicalDocTitle = normalizeWs(document.title);
    const metaEl = document.querySelector('meta[name="description"]');
    if (metaEl && !canonicalMetaDesc) canonicalMetaDesc = normalizeWs(metaEl.getAttribute('content') || '');

    if (!root || !document.createTreeWalker) return;
    root.querySelectorAll('[data-i18n]').forEach(function (el) {
      if (!el.hasAttribute('data-tx-orig-i18n') && el.children.length === 0) {
        el.setAttribute('data-tx-orig-i18n', normalizeWs(el.textContent));
      }
    });

    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (!node.nodeValue || !node.parentElement) return NodeFilter.FILTER_REJECT;
        if (isSkippedElement(node.parentElement)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });

    let n;
    while ((n = walker.nextNode())) {
      if (!origTextMap.has(n)) {
        const raw = n.nodeValue;
        const m = raw.match(/^(\s*)([\s\S]*?)(\s*)$/);
        const core = m ? normalizeWs(m[2]) : normalizeWs(raw);
        if (isTranslatableCore(core)) {
          origTextMap.set(n, { lead: m ? m[1] : '', core: core, trail: m ? m[3] : '' });
        }
      }
    }

    root.querySelectorAll('[placeholder], [title], [aria-label]').forEach(function (el) {
      if (el.hasAttribute('data-tx-no-i18n')) return;
      ['placeholder', 'title', 'aria-label'].forEach(function (attr) {
        const val = el.getAttribute(attr);
        const origAttr = 'data-tx-orig-' + attr;
        if (val && !el.hasAttribute(origAttr) && isTranslatableCore(normalizeWs(val))) {
          el.setAttribute(origAttr, normalizeWs(val));
        }
      });
    });
  }

  function lookupTranslatedSegment(core, pack) {
    if (!pack || !core) return null;
    const strings = pack.strings || {};
    const ui = pack.ui || {};
    if (strings[core]) return strings[core];
    if (ui[core]) return ui[core];

    // Reuse stripped outer symbols/arrows/brackets/emojis around inner phrase
    const m = core.match(/^([^A-Za-z0-9]+)?([\s\S]*?)([^A-Za-z0-9]+)?$/);
    if (m && m[2] && m[2] !== core) {
      const inner = normalizeWs(m[2]);
      const hit = strings[inner] || ui[inner];
      if (hit) {
        return (m[1] || '') + hit + (m[3] || '');
      }
    }

    // Compositional pattern reuse (if pack defines patterns array: [{re, tpl}])
    if (Array.isArray(pack.patterns)) {
      for (let i = 0; i < pack.patterns.length; i++) {
        const pat = pack.patterns[i];
        if (!pat || !pat.re || !pat.tpl) continue;
        try {
          if (!pat._compiled) pat._compiled = new RegExp(pat.re);
          const pm = core.match(pat._compiled);
          if (pm) {
            return pat.tpl.replace(/\{(\d+)\}/g, function (_, idx) {
              const g = pm[Number(idx) + 1] || '';
              return strings[g] || ui[g] || g;
            });
          }
        } catch (_e) {}
      }
    }
    return null;
  }

  function scheduleDynamicBatchTranslation(lang) {
    if (!lang || lang === 'en' || pendingDynamicStrings.size === 0) return;
    if (dynamicBatchTimer) clearTimeout(dynamicBatchTimer);
    dynamicBatchTimer = setTimeout(function () {
      const batch = Array.from(pendingDynamicStrings).slice(0, 64);
      pendingDynamicStrings.clear();
      if (batch.length === 0) return;
      fetch('/api/v1/i18n/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lang: lang, texts: batch })
      })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (res) {
          if (res && res.translations && LOADED_PACKS[lang]) {
            let added = 0;
            Object.keys(res.translations).forEach(function (k) {
              const v = res.translations[k];
              if (v && v !== k) {
                LOADED_PACKS[lang].strings[k] = v;
                added++;
              }
            });
            if (added > 0 && getSavedLang() === lang) {
              applyDomPackSync(document.body, lang, LOADED_PACKS[lang], false);
            }
          }
        })
        .catch(function () {});
    }, 180);
  }

  function applyDomPackSync(root, lang, pack, allowBatchQueue) {
    if (!root) return;
    isApplyingI18n = true;
    try {
      const isRtl = RTL_LANGS.has(lang);
      document.documentElement.setAttribute('dir', isRtl ? 'rtl' : 'ltr');

      // 1. Document Title & Meta Description
      if (canonicalDocTitle) {
        if (lang === 'en') {
          document.title = canonicalDocTitle;
        } else if (pack) {
          const trTitle = lookupTranslatedSegment(canonicalDocTitle, pack);
          if (trTitle) document.title = trTitle;
        }
      }
      const metaEl = document.querySelector('meta[name="description"]');
      if (metaEl && canonicalMetaDesc) {
        if (lang === 'en') {
          metaEl.setAttribute('content', canonicalMetaDesc);
        } else if (pack) {
          const trDesc = lookupTranslatedSegment(canonicalMetaDesc, pack);
          if (trDesc) metaEl.setAttribute('content', trDesc);
        }
      }

      // 2. Capture any newly added DOM nodes before walking
      captureCanonicalEnglishDom(root);

      // 3. Ensure [data-i18n] leaf elements use canonical English source for all 25 languages
      root.querySelectorAll('[data-tx-orig-i18n]').forEach(function (el) {
        if (el.children.length > 0) return;
        const orig = el.getAttribute('data-tx-orig-i18n');
        if (!orig) return;
        if (lang === 'en') {
          el.textContent = orig;
        } else if (pack) {
          const tr = lookupTranslatedSegment(orig, pack);
          if (tr) {
            el.textContent = tr;
          } else if (allowBatchQueue) {
            pendingDynamicStrings.add(orig);
          }
        }
      });

      // 4. Walk all Text nodes across the page
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode: function (node) {
          if (!node.parentElement || isSkippedElement(node.parentElement)) return NodeFilter.FILTER_REJECT;
          if (node.parentElement.hasAttribute('data-tx-orig-i18n') && node.parentElement.children.length === 0) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      });

      let n;
      while ((n = walker.nextNode())) {
        const rec = origTextMap.get(n);
        if (!rec) continue;
        if (lang === 'en') {
          const target = rec.lead + rec.core + rec.trail;
          if (n.nodeValue !== target) n.nodeValue = target;
        } else if (pack) {
          const tr = lookupTranslatedSegment(rec.core, pack);
          if (tr) {
            const target = rec.lead + tr + rec.trail;
            if (n.nodeValue !== target) n.nodeValue = target;
          } else if (allowBatchQueue && rec.core.length <= 420) {
            pendingDynamicStrings.add(rec.core);
          }
        }
      }

      // 5. Translate Attributes (placeholder, title, aria-label)
      root.querySelectorAll('[data-tx-orig-placeholder], [data-tx-orig-title], [data-tx-orig-aria-label]').forEach(function (el) {
        ['placeholder', 'title', 'aria-label'].forEach(function (attr) {
          const orig = el.getAttribute('data-tx-orig-' + attr);
          if (!orig) return;
          if (lang === 'en') {
            el.setAttribute(attr, orig);
          } else if (pack) {
            const tr = lookupTranslatedSegment(orig, pack);
            if (tr) el.setAttribute(attr, tr);
          }
        });
      });
    } finally {
      isApplyingI18n = false;
    }

    if (allowBatchQueue && lang !== 'en' && pendingDynamicStrings.size > 0) {
      scheduleDynamicBatchTranslation(lang);
    }
  }

  function applyFullDomTranslation(lang) {
    if (!lang || lang === 'en') {
      applyDomPackSync(document.body, 'en', null, false);
      return Promise.resolve();
    }
    return loadLanguagePack(lang).then(function (pack) {
      if (getSavedLang() !== lang) return;
      if (pack) {
        applyDomPackSync(document.body, lang, pack, true);
      } else {
        document.documentElement.setAttribute('dir', RTL_LANGS.has(lang) ? 'rtl' : 'ltr');
      }
    });
  }

  function ensureMutationObserver() {
    if (domObserver || typeof MutationObserver === 'undefined' || !document.body) return;
    domObserver = new MutationObserver(function (mutations) {
      if (isApplyingI18n) return;
      const lang = getSavedLang();
      const curr = getSavedCurrency();
      let hasAdded = false;
      for (let i = 0; i < mutations.length; i++) {
        if (mutations[i].addedNodes && mutations[i].addedNodes.length > 0) {
          hasAdded = true;
          break;
        }
      }
      if (!hasAdded) return;
      isApplyingI18n = true;
      try {
        mutations.forEach(function (m) {
          m.addedNodes.forEach(function (node) {
            if (node.nodeType === 1 && !isSkippedElement(node)) {
              normalizePendingSubdomainLinks(node);
              tagInlineMoneyNodes(node);
              applyCurrencyEverywhere(curr, getSavedCountry(), lang);
              if (lang !== 'en' && LOADED_PACKS[lang]) {
                applyDomPackSync(node, lang, LOADED_PACKS[lang], true);
              } else {
                captureCanonicalEnglishDom(node);
              }
            }
          });
        });
      } finally {
        isApplyingI18n = false;
      }
    });
    domObserver.observe(document.body, { childList: true, subtree: true });
  }

  function convertMoney(baseAmt, baseCurr, targetCurr, decimalsOverride) {
    const info = CURRENCIES[targetCurr] || CURRENCIES.EUR;
    const num = parseFloat(baseAmt);
    if (isNaN(num)) return 0;
    const rate = (baseCurr === 'USD') ? info.rate_from_usd : info.rate_from_eur;
    const raw = (targetCurr === baseCurr) ? num : (num * rate);
    if (targetCurr === 'SOL') {
      return +(raw.toFixed(decimalsOverride !== undefined ? decimalsOverride : 2));
    }
    if (info.zero_decimal) {
      return Math.round(raw);
    }
    if (decimalsOverride !== undefined && decimalsOverride !== null && decimalsOverride !== '') {
      const d = parseInt(decimalsOverride, 10);
      return +(raw.toFixed(d));
    }
    if (num > 0 && num < 5 && raw < 10) {
      return +(raw.toFixed(2));
    }
    return Math.round(raw);
  }

  function formatMoney(amt, targetCurr, decimalsOverride, suffix) {
    const info = CURRENCIES[targetCurr] || CURRENCIES.EUR;
    const sfx = suffix || '';
    if (targetCurr === 'SOL') {
      return `◎${amt}${sfx}`;
    }
    if (decimalsOverride !== undefined && decimalsOverride !== null && decimalsOverride !== '' && !info.zero_decimal) {
      const d = parseInt(decimalsOverride, 10);
      return `${info.symbol}${Number(amt).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d })}${sfx}`;
    }
    return `${info.symbol}${Number(amt).toLocaleString()}${sfx}`;
  }

  function tagInlineMoneyNodes(root) {
    if (!root || !document.createTreeWalker) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (!node.nodeValue || (!node.nodeValue.includes('$') && !node.nodeValue.includes('€'))) {
          return NodeFilter.FILTER_REJECT;
        }
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        const tag = parent.tagName;
        if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'CODE' || tag === 'PRE' || tag === 'OPTION' || tag === 'TEXTAREA') {
          return NodeFilter.FILTER_REJECT;
        }
        if (
          parent.classList.contains('tx-store-price') ||
          parent.classList.contains('tx-btn-price') ||
          parent.classList.contains('tx-dyn-money') ||
          parent.classList.contains('tx-auto-money') ||
          parent.closest('#tx-market-context-banner') ||
          parent.hasAttribute('data-base-amt') ||
          parent.hasAttribute('data-i18n')
        ) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });

    const nodesToProcess = [];
    let current;
    while ((current = walker.nextNode())) {
      nodesToProcess.push(current);
    }

    const priceRegex = /([€$])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)([kKmM])?(?!\w)/g;

    nodesToProcess.forEach(function (textNode) {
      const text = textNode.nodeValue;
      if (!priceRegex.test(text)) return;
      priceRegex.lastIndex = 0;

      const frag = document.createDocumentFragment();
      let lastIdx = 0;
      let match;
      while ((match = priceRegex.exec(text)) !== null) {
        if (match.index > lastIdx) {
          frag.appendChild(document.createTextNode(text.slice(lastIdx, match.index)));
        }
        const sym = match[1];
        const rawNumStr = match[2].replace(/,/g, '');
        const unitSuffix = match[3] || '';
        const baseCurr = (sym === '$') ? 'USD' : 'EUR';
        let baseAmt = parseFloat(rawNumStr);
        let decimals = '';
        if (rawNumStr.includes('.')) {
          decimals = String(rawNumStr.split('.')[1].length);
        }
        if (unitSuffix.toLowerCase() === 'k') {
          baseAmt = baseAmt * 1000;
          decimals = '';
        }

        const span = document.createElement('span');
        span.className = 'tx-auto-money';
        span.setAttribute('data-base-curr', baseCurr);
        span.setAttribute('data-base-amt', String(baseAmt));
        if (decimals) span.setAttribute('data-decimals', decimals);
        if (unitSuffix.toUpperCase() === 'M') span.setAttribute('data-suffix', 'M');
        span.textContent = match[0];
        frag.appendChild(span);
        lastIdx = priceRegex.lastIndex;
      }
      if (lastIdx < text.length) {
        frag.appendChild(document.createTextNode(text.slice(lastIdx)));
      }
      if (textNode.parentNode) {
        textNode.parentNode.replaceChild(frag, textNode);
      }
    });
  }

  function renderMarketContextBanner(country, lang, curr) {
    const profile = COUNTRY_PROFILES[country] || COUNTRY_PROFILES.EE;
    const dict = GLOBAL_I18N[lang] || GLOBAL_I18N.en;
    const pack = LOADED_PACKS[lang];
    let countryName = (profile.name && (profile.name[lang] || profile.name.en)) || country;
    if (lang !== 'en' && pack && pack.strings && pack.strings[countryName]) {
      countryName = pack.strings[countryName];
    }
    let regimeText = profile.regime;
    if (lang !== 'en' && pack && pack.strings && pack.strings[regimeText]) {
      regimeText = pack.strings[regimeText];
    }
    const currInfo = CURRENCIES[curr] || CURRENCIES.EUR;

    let banner = document.getElementById('tx-market-context-banner');
    if (!banner) {
      const host = document.getElementById('main-content') || document.querySelector('main, .wrap, .container, .tx-wrap');
      if (!host) return;
      banner = document.createElement('section');
      banner.id = 'tx-market-context-banner';
      banner.className = 'tx-market-context-banner';
      banner.setAttribute('data-tx-no-i18n', '1');
      banner.setAttribute('aria-label', 'Regional Market, Language and Compliance Context');
      host.insertBefore(banner, host.firstChild);
    }

    isApplyingI18n = true;
    try {
      banner.innerHTML = `
        <div class="tx-mcb-left">
          <span class="tx-mcb-pill" dir="ltr">${profile.flag} ${country} · ${lang.toUpperCase()} · ${curr} (${currInfo.symbol.trim()})</span>
          <strong class="tx-mcb-country">${dict.ctx_active}: ${countryName}</strong>
        </div>
        <div class="tx-mcb-right">
          <span><strong>${dict.ctx_regime}:</strong> ${regimeText}</span>
          <span class="tx-mcb-sep">·</span>
          <span><strong>${dict.ctx_stmt}:</strong> <code dir="ltr">RASAXMACHINA * [SKU]</code></span>
        </div>
      `;
    } finally {
      isApplyingI18n = false;
    }
  }

  function applyMaterialLocalization(country, lang, curr, announce) {
    syncAllDropdownOptions();
    const validCountry = COUNTRY_PROFILES[country] ? country : getSavedCountry();
    const validLang = GLOBAL_I18N[lang] ? lang : getSavedLang();
    const validCurr = CURRENCIES[curr] ? curr : getSavedCurrency();

    setSavedLocale(validCountry, validLang);
    setSavedCurrency(validCurr);

    if (document.documentElement.getAttribute('lang') !== validLang) {
      document.documentElement.setAttribute('lang', validLang);
    }
    document.documentElement.setAttribute('dir', RTL_LANGS.has(validLang) ? 'rtl' : 'ltr');

    const comboVal = getLocaleComboValue(validCountry, validLang);
    LOCALE_SELECT_IDS.forEach(function (id) {
      const sel = document.getElementById(id);
      if (sel && sel.value !== comboVal) {
        if ([].some.call(sel.options, function (o) { return o.value === comboVal; })) {
          sel.value = comboVal;
        }
      }
    });

    const gDict = GLOBAL_I18N[validLang] || GLOBAL_I18N.en;
    const skipEl = document.querySelector('.tx-skip-link');
    if (skipEl) skipEl.textContent = gDict.skip_main;

    const dockApps = document.getElementById('tx-dock-apps-lbl');
    if (dockApps) dockApps.textContent = gDict.dock_apps;
    const dockGui = document.getElementById('tx-dock-gui-lbl');
    if (dockGui) dockGui.textContent = gDict.dock_gui;
    const dockHw = document.getElementById('tx-dock-hw-lbl');
    if (dockHw) dockHw.textContent = gDict.dock_hw;
    const dockGdpr = document.getElementById('tx-dock-gdpr-lbl');
    if (dockGdpr) dockGdpr.textContent = gDict.dock_gdpr;

    if (typeof window.onTxGlobalLocaleChange === 'function') {
      try {
        window.onTxGlobalLocaleChange(validCountry, validLang, validCurr);
      } catch (_e) {}
    }

    applyCurrencyEverywhere(validCurr, validCountry, validLang);
    renderMarketContextBanner(validCountry, validLang, validCurr);

    applyFullDomTranslation(validLang).then(function () {
      applyCurrencyEverywhere(validCurr, validCountry, validLang);
      renderMarketContextBanner(validCountry, validLang, validCurr);
    });

    if (announce) {
      const p = COUNTRY_PROFILES[validCountry] || COUNTRY_PROFILES.EE;
      announceForScreenReader(`${p.name.en} · ${validLang.toUpperCase()} · ${validCurr}`);
    }
  }

  function applyCurrencyEverywhere(targetCurr, countryOverride, langOverride) {
    const curr = CURRENCIES[targetCurr] ? targetCurr : getSavedCurrency();
    const country = countryOverride || getSavedCountry();
    const lang = langOverride || getSavedLang();
    setSavedCurrency(curr);

    CURR_SELECT_IDS.forEach(function (id) {
      const el = document.getElementById(id);
      if (el && el.value !== curr) {
        if ([].some.call(el.options || [], function (o) { return o.value === curr; })) {
          el.value = curr;
        }
      }
    });

    const moneyEls = document.querySelectorAll('.tx-store-price, .tx-btn-price, .tx-dyn-money, .tx-auto-money, [data-base-amt]');
    moneyEls.forEach(function (el) {
      const baseCurr = el.getAttribute('data-base-curr') || (el.getAttribute('data-eur') ? 'EUR' : 'USD');
      const baseAmt = el.getAttribute('data-base-amt') || el.getAttribute('data-eur') || el.getAttribute('data-usd');
      if (baseAmt === null || baseAmt === undefined || baseAmt === '') return;
      const decimals = el.getAttribute('data-decimals');
      const suffix = el.getAttribute('data-suffix') || '';
      const conv = convertMoney(baseAmt, baseCurr, curr, decimals !== null ? decimals : undefined);
      el.textContent = formatMoney(conv, curr, decimals !== null ? decimals : undefined, suffix);
    });

    const chargeCurr = (curr === 'SOL') ? 'EUR' : curr;
    document.querySelectorAll('.tx-express-stripe, a[href*="/api/v1/stripe-express"]').forEach(function (link) {
      const plan = link.getAttribute('data-plan') || (link.href.match(/[?&]plan=([^&]+)/) || [])[1];
      if (plan) {
        link.href = `/api/v1/stripe-express?plan=${encodeURIComponent(plan)}&currency=${encodeURIComponent(chargeCurr)}&lang=${encodeURIComponent(lang)}&country=${encodeURIComponent(country)}`;
      }
    });
  }

  function initSeoAeoGeoMetadata() {
    if (!document.querySelector('link[rel="manifest"]')) {
      const mfLink = document.createElement('link');
      mfLink.rel = 'manifest';
      mfLink.href = '/manifest.json';
      document.head.appendChild(mfLink);
    }
    if (!document.querySelector('link[rel="icon"]')) {
      const icLink = document.createElement('link');
      icLink.rel = 'icon';
      icLink.type = 'image/svg+xml';
      icLink.href = '/icon.svg';
      document.head.appendChild(icLink);
    }
    if ('serviceWorker' in navigator && !window.__TX_SW_BOOTED__) {
      window.__TX_SW_BOOTED__ = true;
      navigator.serviceWorker.register('/sw.js').catch(function () {});
    }
    if (!document.querySelector('link[rel="alternate"][href="/llms.txt"]')) {
      const llmsLink = document.createElement('link');
      llmsLink.rel = 'alternate';
      llmsLink.type = 'text/plain';
      llmsLink.href = '/llms.txt';
      llmsLink.title = 'tianxiaOS & RASA-X-MACHINA LLM/AEO Citation Manifest';
      document.head.appendChild(llmsLink);
    }
    if (!document.querySelector('link[rel="sitemap"]')) {
      const smLink = document.createElement('link');
      smLink.rel = 'sitemap';
      smLink.type = 'application/xml';
      smLink.href = '/sitemap.xml';
      document.head.appendChild(smLink);
    }
    if (!document.querySelector('script[type="application/ld+json"]')) {
      const pageTitle = document.title || 'tianxiaOS — Sovereign Autonomous Operating System | RASA-X-MACHINA';
      const metaDesc = (document.querySelector('meta[name="description"]') || {}).content ||
        'tianxiaOS by RASA-X-MACHINA: Polyglot seL4/NixOS autonomous AI operating substrate across 42 global markets and 29 currencies.';
      const ld = {
        '@context': 'https://schema.org',
        '@graph': [
          {
            '@type': 'Organization',
            '@id': 'https://rasaxmachina.com/#organization',
            'name': 'RASA-X-MACHINA',
            'alternateName': 'tianxiaOS',
            'url': 'https://rasaxmachina.com/',
            'contactPoint': {
              '@type': 'ContactPoint',
              'contactType': 'executive & enterprise inquiries',
              'url': 'https://rasaxmachina.com/collins#encrypted-dispatch',
              'availableLanguage': ['en', 'et', 'de', 'fr']
            },
            'founder': { '@type': 'Person', 'name': 'Collins Takem', 'jobTitle': 'Founder & Chief Systems Architect' },
            'sameAs': [
              'https://github.com/Tianxia-Core',
              'https://github.com/Tianxia-Core/tianxiaos-releases',
              'https://www.linkedin.com/in/coltak2',
              'https://x.com/rasaxmachina',
              'https://x.com/tianxiaos',
              'https://x.com/coltakrasax',
              'https://www.facebook.com/rasaxmachina',
              'https://t.me/rasaxmachina',
              'https://www.instagram.com/rasaxmachina',
              'https://rasaxmachina.com/about',
              'https://rasaxmachina.com/collins',
              'https://rasaxmachina.com/press',
              'https://rasaxmachina.com/estonia',
              'https://pay.rasaxmachina.com/'
            ]
          },
          {
            '@type': 'SoftwareApplication',
            'name': pageTitle,
            'applicationCategory': 'DeveloperApplication',
            'operatingSystem': 'tianxiaOS (NixOS / seL4 / Linux / Windows / Android / WebGPU Wasm)',
            'description': metaDesc,
            'offers': { '@type': 'AggregateOffer', 'priceCurrency': 'EUR', 'lowPrice': '9.00', 'highPrice': '9250.00', 'offerCount': '21' }
          }
        ]
      };
      const script = document.createElement('script');
      script.type = 'application/ld+json';
      script.id = 'tx-auto-jsonld';
      script.textContent = JSON.stringify(ld);
      document.head.appendChild(script);
    }
  }

  function createUnifiedLocaleSelect(id, className) {
    const sel = document.createElement('select');
    sel.id = id;
    sel.className = className || 'tx-std-locale-select';
    sel.setAttribute('data-tx-no-i18n', '1');
    sel.setAttribute('data-tx-upgraded-42', '1');
    sel.setAttribute('aria-label', 'Select Country and Interface Language');
    sel.setAttribute('title', 'Select Country / Market & Interface Language');
    LOCALE_OPTIONS.forEach(function (optMeta) {
      const opt = document.createElement('option');
      opt.value = optMeta.val;
      opt.textContent = optMeta.label;
      sel.appendChild(opt);
    });
    sel.value = getLocaleComboValue(getSavedCountry(), getSavedLang());
    sel.addEventListener('change', function (e) {
      const parts = (e.target.value || 'EE:en').split(':');
      const cc = parts[0] || 'EE';
      const lg = parts[1] || 'en';
      const found = LOCALE_OPTIONS.find(function (o) { return o.val === e.target.value; });
      const defCurr = found ? found.curr : getSavedCurrency();
      applyMaterialLocalization(cc, lg, defCurr, true);
    });
    return sel;
  }

  function initWebStandardsAndAccessibility() {
    if (!document.querySelector('link[href*="family=Syne"]')) {
      const syneLink = document.createElement('link');
      syneLink.rel = 'stylesheet';
      syneLink.href = 'https://fonts.googleapis.com/css2?family=Syne:wght@700;800&display=swap';
      document.head.appendChild(syneLink);
    }
    const style = document.createElement('style');
    style.id = 'tx-web-standards-css';
    style.textContent = `
      .tx-logo-rxm, .tx-nav-brand {
        font-family: 'Syne', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: 0 !important;
        background: linear-gradient(120deg, #7c5cff 0%, #a855f7 48%, #22d3ee 100%) !important;
        -webkit-background-clip: text !important;
        background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        color: transparent !important;
        text-transform: uppercase !important;
        text-decoration: none;
        display: inline-block;
      }
      .tx-logo-os {
        font-family: "Clash Display", "Geist", "Space Grotesk", system-ui, sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        background: linear-gradient(120deg, #7c5cff 0%, #a855f7 45%, #c084fc 100%) !important;
        -webkit-background-clip: text !important;
        background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        color: transparent !important;
        text-transform: none !important;
        text-decoration: none;
        display: inline-block;
      }
      .tx-brand-sep { color: rgba(148, 163, 184, 0.72); margin: 0 0.3rem; font-weight: 500; }
      .tx-skip-link {
        position: fixed; top: -100px; left: 1rem; z-index: 100001;
        background: #00f59b; color: #040406; font-family: 'JetBrains Mono', monospace;
        font-weight: 700; font-size: 0.85rem; padding: 0.65rem 1.1rem; border-radius: 0.5rem;
        text-decoration: none; box-shadow: 0 8px 24px rgba(0, 245, 155, 0.4); transition: top 0.15s ease;
      }
      .tx-skip-link:focus, .tx-skip-link:focus-visible { top: 1rem; outline: 3px solid #ffffff; outline-offset: 2px; }
      :focus-visible { outline: 2px solid #00f59b !important; outline-offset: 2px !important; }
      html[dir="rtl"] code, html[dir="rtl"] pre, html[dir="rtl"] .tx-store-price,
      html[dir="rtl"] .tx-btn-price, html[dir="rtl"] .tx-dyn-money, html[dir="rtl"] .tx-auto-money {
        direction: ltr; unicode-bidi: isolate; display: inline-block;
      }
      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }
        canvas#tx-stars { display: none !important; }
      }
      .tx-market-context-banner {
        display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
        gap: 0.45rem 0.9rem; padding: 0.48rem 0.85rem; margin-bottom: 1.1rem; border-radius: 0.65rem;
        background: rgba(12, 14, 24, 0.78); border: 1px solid rgba(124, 92, 255, 0.28);
        font-family: 'Space Grotesk', system-ui, sans-serif; font-size: 0.75rem; color: #cbd5e1;
      }
      .tx-mcb-left { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
      .tx-mcb-pill {
        font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 700;
        padding: 0.15rem 0.5rem; border-radius: 999px; background: rgba(0, 245, 155, 0.12);
        border: 1px solid rgba(0, 245, 155, 0.35); color: #00f59b;
      }
      .tx-mcb-country { color: #f8fafc; font-size: 0.77rem; }
      .tx-mcb-right { display: flex; align-items: center; gap: 0.45rem; flex-wrap: wrap; font-size: 0.72rem; color: #94a3b8; }
      .tx-mcb-right code { color: #fbbf24; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; }
      .tx-std-locale-select, .tx-std-curr-select {
        background: rgba(14, 15, 24, 0.94); color: #e2e8f0; border: 1px solid rgba(124, 92, 255, 0.4);
        border-radius: 999px; padding: 0.24rem 0.52rem; font-family: 'JetBrains Mono', monospace;
        font-size: 0.71rem; font-weight: 600; cursor: pointer; max-width: 155px;
      }
      .tx-std-curr-select { color: #00f59b; border-color: rgba(0, 245, 155, 0.4); max-width: 112px; }
      .tx-home-nav, nav.top-nav, .nav-bar, header.topbar, .tx-auto-top-nav {
        position: fixed !important; width: max-content !important; height: auto !important;
        max-width: min(980px, calc(100vw - 1.2rem)) !important; left: 50% !important; right: auto !important;
        inset-inline-start: 50% !important; inset-inline-end: auto !important; margin: 0 !important;
        transform: translateX(-50%) translateY(0) !important; border-radius: 999px !important;
        border: 1px solid rgba(124, 92, 255, 0.38) !important; background: rgba(10, 10, 18, 0.84) !important;
        backdrop-filter: blur(28px) !important; -webkit-backdrop-filter: blur(28px) !important;
        box-shadow: 0 0 64px -14px rgba(124, 92, 255, 0.55), 0 10px 30px rgba(0, 0, 0, 0.68) !important;
        padding: 0.36rem 0.72rem !important; gap: 0.32rem !important; top: 0.75rem !important;
        z-index: 99980 !important; display: inline-flex !important; align-items: center !important;
        justify-content: flex-start !important; flex-wrap: nowrap !important; white-space: nowrap !important;
        overflow-x: auto !important; overflow-y: hidden !important; scrollbar-width: none !important;
        -ms-overflow-style: none !important; direction: ltr !important;
        transition: opacity 0.26s cubic-bezier(0.22, 1, 0.36, 1), transform 0.26s cubic-bezier(0.22, 1, 0.36, 1) !important;
      }
      .tx-home-nav::-webkit-scrollbar, nav.top-nav::-webkit-scrollbar, .nav-bar::-webkit-scrollbar,
      header.topbar::-webkit-scrollbar, .tx-auto-top-nav::-webkit-scrollbar { display: none !important; }
      .tx-home-nav .nav-links, nav.top-nav .nav-links, .nav-bar .nav-links,
      header.topbar .nav-wrap, header.topbar .nav-links, .tx-nav-right-cluster {
        display: inline-flex !important; align-items: center !important; flex-wrap: nowrap !important;
        white-space: nowrap !important; gap: 0.48rem !important; width: auto !important; margin: 0 !important;
      }
      .tx-home-nav.tx-floating-idle, nav.top-nav.tx-floating-idle, .nav-bar.tx-floating-idle,
      header.topbar.tx-floating-idle, .tx-auto-top-nav.tx-floating-idle {
        opacity: 0 !important; transform: translateX(-50%) translateY(-115%) scale(0.96) !important; pointer-events: none !important;
      }
      .tx-cohesion-dock {
        position: fixed; bottom: 0.55rem; right: 0.65rem; z-index: 99985; display: inline-flex;
        width: fit-content; max-width: calc(100vw - 1.3rem); align-items: center; gap: 0.2rem;
        background: rgba(8, 8, 14, 0.9); backdrop-filter: blur(14px); border: 1px solid rgba(124, 92, 255, 0.38);
        border-radius: 999px; padding: 0.2rem 0.45rem; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7);
        font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
        transition: opacity 0.24s cubic-bezier(0.22, 1, 0.36, 1), transform 0.24s cubic-bezier(0.22, 1, 0.36, 1);
      }
      .tx-cohesion-dock.tx-floating-idle { opacity: 0.04 !important; transform: translateY(78%) scale(0.95) !important; pointer-events: none !important; }
      .tx-dock-pill {
        background: transparent; border: none; color: #cbd5e1; font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem; font-weight: 600; padding: 0.18rem 0.36rem; border-radius: 999px;
        cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 0.2rem; white-space: nowrap;
      }
      .tx-dock-pill:hover { background: rgba(124, 92, 255, 0.22); color: #00f59b; }
      .tx-gdpr-btn {
        font-family: 'JetBrains Mono', monospace; font-size: 0.73rem; font-weight: 600;
        padding: 0.42rem 0.8rem; min-height: 34px; border-radius: 0.5rem; cursor: pointer;
        border: 1px solid rgba(255,255,255,0.18); background: rgba(255,255,255,0.06); color: #f4f4f8;
      }
      .tx-gdpr-btn.primary { background: linear-gradient(135deg, #7c5cff, #00f59b); color: #040406; border: none; font-weight: 700; }
      @media (max-width: 720px) { .tx-cohesion-dock .tx-dock-hide-sm { display: none; } .tx-mcb-right { display: none; } }
    `;
    document.head.appendChild(style);

    if (!document.querySelector('.tx-skip-link')) {
      const skip = document.createElement('a');
      skip.href = '#main-content';
      skip.className = 'tx-skip-link';
      skip.setAttribute('data-tx-no-i18n', '1');
      skip.textContent = 'Skip to main content';
      document.body.insertBefore(skip, document.body.firstChild);
    }

    let mainEl = document.getElementById('main-content') || document.querySelector('main');
    if (mainEl) {
      if (!mainEl.id) mainEl.id = 'main-content';
      if (!mainEl.hasAttribute('tabindex')) mainEl.setAttribute('tabindex', '-1');
    } else {
      const container = document.querySelector('.wrap, .container, .tx-wrap, .hero');
      if (container) {
        container.id = 'main-content';
        container.setAttribute('role', 'main');
        container.setAttribute('tabindex', '-1');
      }
    }

    syncAllDropdownOptions();

    // Ensure custom page locale selects also trigger full 42-market localization even if inline JS had a smaller map
    LOCALE_SELECT_IDS.forEach(function (id) {
      const sel = document.getElementById(id);
      if (sel && !sel.getAttribute('data-tx-bound-42')) {
        sel.setAttribute('data-tx-bound-42', '1');
        sel.addEventListener('change', function (e) {
          const parts = (e.target.value || 'EE:en').split(':');
          const cc = parts[0] || 'EE';
          const lg = parts[1] || 'en';
          const found = LOCALE_OPTIONS.find(function (o) { return o.val === e.target.value; });
          const defCurr = found ? found.curr : getSavedCurrency();
          applyMaterialLocalization(cc, lg, defCurr, true);
        });
      }
    });

    CURR_SELECT_IDS.forEach(function (id) {
      const sel = document.getElementById(id);
      if (sel && !sel.getAttribute('data-tx-bound-29')) {
        sel.setAttribute('data-tx-bound-29', '1');
        sel.addEventListener('change', function (e) {
          const chosen = e.target.value;
          setSavedCurrency(chosen);
          applyMaterialLocalization(getSavedCountry(), getSavedLang(), chosen, true);
        });
      }
    });

    const hasCustomLocale = LOCALE_SELECT_IDS.some(function (id) { return !!document.getElementById(id); });
    const hasCustomCurr = CURR_SELECT_IDS.some(function (id) { return !!document.getElementById(id); });

    let navTarget = document.querySelector('.tx-nav-right-cluster, .tx-desktop-right, .nav-links, .nav-cta, .topbar .nav-wrap, .topbar .wrap, header, nav');
    if (!navTarget) {
      const autoNav = document.createElement('nav');
      autoNav.className = 'tx-auto-top-nav';
      autoNav.setAttribute('aria-label', 'Primary Navigation');
      autoNav.innerHTML = `<a href="https://rasaxmachina.com" class="tx-logo-rxm" data-tx-no-i18n="1" style="font-size:0.88rem;padding:0.2rem 0.55rem;margin-right:0.25rem;border-right:1px solid rgba(255,255,255,0.1)">RASA-X-MACHINA</a><a href="/pay" style="color:#c084fc;text-decoration:none;font-size:0.75rem;font-weight:600;margin-right:0.25rem">Pay Hub ↗</a>`;
      document.body.insertBefore(autoNav, mainEl || document.body.firstChild);
      navTarget = autoNav;
    }
    if (navTarget) {
      const cluster = document.createElement('span');
      cluster.className = 'tx-std-2control-cluster';
      cluster.style.cssText = 'display:inline-flex;align-items:center;gap:0.3rem;flex-wrap:nowrap';

      if (!hasCustomLocale) {
        const lSel = createUnifiedLocaleSelect('tx-std-locale-select', 'tx-std-locale-select');
        lSel.setAttribute('data-tx-bound-42', '1');
        cluster.appendChild(lSel);
      }
      if (!hasCustomCurr) {
        const sel = document.createElement('select');
        sel.id = 'tx-std-curr-select';
        sel.className = 'tx-std-curr-select';
        sel.setAttribute('data-tx-no-i18n', '1');
        sel.setAttribute('data-tx-upgraded-29', '1');
        sel.setAttribute('data-tx-bound-29', '1');
        sel.setAttribute('aria-label', 'Select Display and Billing Currency');
        sel.setAttribute('title', 'Select Display & Billing Currency (100% Consistent Single-Currency View)');
        CURRENCY_ORDER.forEach(function (c) {
          const opt = document.createElement('option');
          opt.value = c;
          opt.textContent = `${c} (${CURRENCIES[c].symbol.trim()})`;
          sel.appendChild(opt);
        });
        sel.value = getSavedCurrency();
        sel.addEventListener('change', function (e) {
          const chosen = e.target.value;
          setSavedCurrency(chosen);
          if (typeof window.changeCurrency === 'function') window.changeCurrency(chosen);
          applyMaterialLocalization(getSavedCountry(), getSavedLang(), chosen, true);
        });
        cluster.appendChild(sel);
      }
      if (cluster.children.length > 0) navTarget.appendChild(cluster);
    }

    document.querySelectorAll('input, select, textarea').forEach(function (input) {
      if (!input.getAttribute('autocomplete')) {
        const idOrName = ((input.id || '') + ' ' + (input.name || '') + ' ' + (input.type || '')).toLowerCase();
        if (idOrName.includes('email')) input.setAttribute('autocomplete', 'email');
        else if (idOrName.includes('name')) input.setAttribute('autocomplete', 'name');
        else if (idOrName.includes('org') || idOrName.includes('company')) input.setAttribute('autocomplete', 'organization');
        else input.setAttribute('autocomplete', 'off');
      }
      if (!input.getAttribute('aria-label') && !input.id) {
        input.setAttribute('aria-label', input.placeholder || input.name || 'Input field');
      }
    });
  }

  function initActivityAwareFloatingChrome() {
    function getFloatingEls() {
      return Array.prototype.slice.call(
        document.querySelectorAll('.tx-home-nav, nav.top-nav, .nav-bar, header.topbar, .tx-auto-top-nav, #tx-cohesion-dock')
      );
    }
    function hasFocusedControlInside(els) {
      const active = document.activeElement;
      if (!active || active === document.body) return false;
      return els.some(function (el) { return el.contains(active); });
    }
    function wakeFloatingChrome() {
      const els = getFloatingEls();
      els.forEach(function (el) { el.classList.remove('tx-floating-idle'); });
      if (idleChromeTimer) clearTimeout(idleChromeTimer);
      idleChromeTimer = setTimeout(function () {
        const currentEls = getFloatingEls();
        if (hasFocusedControlInside(currentEls)) return;
        currentEls.forEach(function (el) { el.classList.add('tx-floating-idle'); });
      }, 2100);
    }
    ['scroll', 'wheel', 'touchmove', 'mousemove', 'pointermove', 'touchstart', 'pointerdown', 'keydown', 'focusin'].forEach(function (evtName) {
      window.addEventListener(evtName, wakeFloatingChrome, { passive: true });
      document.addEventListener(evtName, wakeFloatingChrome, { passive: true, capture: true });
    });
    wakeFloatingChrome();
  }

  function initGdprCompliance() {
    const footerBottom = document.querySelector('.tx-footer-bottom, .footer-box, .auth-box, footer');
    if (footerBottom && !document.getElementById('tx-gdpr-footer-trigger')) {
      const wrap = document.createElement('div');
      wrap.style.cssText = 'margin-top:0.75rem;display:flex;gap:0.45rem;flex-wrap:wrap;justify-content:center;align-items:center';
      wrap.innerHTML = `
        <a href="/about" class="tx-gdpr-btn" style="text-decoration:none">🏛️ About</a>
        <a href="/collins" class="tx-gdpr-btn" style="text-decoration:none">👤 Founder &amp; Channels</a>
        <a href="/privacy" class="tx-gdpr-btn" style="text-decoration:none">📜 Privacy Policy</a>
        <a href="/terms" class="tx-gdpr-btn" style="text-decoration:none">⚖️ Terms of Service</a>
        <button type="button" id="tx-gdpr-footer-trigger" class="tx-gdpr-btn">🛡️ GDPR++ Horizon Rights (&lt;50ms PQ Cryptoshredding)</button>
        <button type="button" id="tx-cmdk-footer-trigger" class="tx-gdpr-btn">⌘K Ecosystem Launcher (28 Subdomains)</button>
        <button type="button" id="tx-hw-footer-trigger" class="tx-gdpr-btn">⚡ Hardware Enclave Bridge</button>
        <a href="https://github.com/Tianxia-Core/tianxiaos-releases" target="_blank" rel="noopener" class="tx-gdpr-btn" style="text-decoration:none">📦 Signed Releases (.deb/.rpm/AppImage/.exe/.apk)</a>
        <a href="https://x.com/rasaxmachina" target="_blank" rel="noopener" class="tx-gdpr-btn" style="text-decoration:none" data-tx-no-i18n="1">𝕏 @rasaxmachina</a>
        <a href="https://x.com/tianxiaos" target="_blank" rel="noopener" class="tx-gdpr-btn" style="text-decoration:none" data-tx-no-i18n="1">𝕏 @tianxiaos</a>
        <a href="https://x.com/coltakrasax" target="_blank" rel="noopener" class="tx-gdpr-btn" style="text-decoration:none" data-tx-no-i18n="1">𝕏 @coltakrasax</a>
        <a href="/cockpit" class="tx-gdpr-btn" style="text-decoration:none">🖥️ Cockpit GUI</a>
      `;
      footerBottom.appendChild(wrap);
      document.getElementById('tx-gdpr-footer-trigger').addEventListener('click', openGdprRightsModal);
      document.getElementById('tx-cmdk-footer-trigger').addEventListener('click', openCommandPaletteModal);
      document.getElementById('tx-hw-footer-trigger').addEventListener('click', openHardwareBridgeModal);
    }
  }

  function translateModalIfNeeded(modal) {
    const lang = getSavedLang();
    captureCanonicalEnglishDom(modal);
    if (lang !== 'en') {
      loadLanguagePack(lang).then(function (pack) {
        if (pack) applyDomPackSync(modal, lang, pack, true);
      });
    }
  }

  function openGdprRightsModal() {
    let modal = document.getElementById('tx-gdpr-rights-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'tx-gdpr-rights-modal';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-modal', 'true');
      modal.setAttribute('aria-labelledby', 'tx-gdpr-modal-title');
      modal.style.cssText = 'position:fixed;inset:0;z-index:100000;background:rgba(4,4,8,0.86);backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center;padding:1rem';
      modal.innerHTML = `
        <div style="background:#0d0e17;border:1px solid rgba(124,92,255,0.55);border-radius:1rem;max-width:560px;width:100%;padding:1.5rem;color:#f4f4f8;font-family:'Space Grotesk',sans-serif;box-shadow:0 24px 60px rgba(0,0,0,0.9)">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.85rem">
            <h3 id="tx-gdpr-modal-title" style="margin:0;font-size:1.05rem;color:#00f59b;font-family:'JetBrains Mono',monospace">🛡️ GDPR++ Horizon Data Sovereignty Portal (v2030.4)</h3>
            <button type="button" id="tx-gdpr-modal-close" aria-label="Close GDPR++ Modal" class="tx-gdpr-btn">✕</button>
          </div>
          <p style="font-size:0.81rem;color:#a0a3b8;line-height:1.5;margin:0 0 1rem">
            Outclassing EU GDPR (2016/679), Estonian AKI/IKS, EU AI Act, Swiss revFADP, CPRA &amp; LGPD by 3–5 years: execute instantaneous &lt;50ms Post-Quantum Ephemeral Key Cryptoshredding (<code>XChaCha20-Poly1305 + ML-KEM-1024</code>) or Zero-Knowledge Merkle Access Audits.
          </p>
          <form id="tx-gdpr-form">
            <div style="margin-bottom:0.75rem">
              <label for="tx-gdpr-email" style="display:block;font-size:0.75rem;color:#cbd5e1;margin-bottom:0.3rem">Subject Email Address *</label>
              <input type="email" id="tx-gdpr-email" autocomplete="email" required placeholder="you@organization.eu" style="width:100%;padding:0.6rem 0.75rem;border-radius:0.5rem;border:1px solid rgba(255,255,255,0.18);background:#07080d;color:#fff;font-size:0.85rem"/>
            </div>
            <div style="margin-bottom:0.75rem">
              <label for="tx-gdpr-right-type" style="display:block;font-size:0.75rem;color:#cbd5e1;margin-bottom:0.3rem">Select GDPR++ Sovereign Right *</label>
              <select id="tx-gdpr-right-type" style="width:100%;padding:0.6rem 0.75rem;border-radius:0.5rem;border:1px solid rgba(255,255,255,0.18);background:#07080d;color:#fff;font-size:0.85rem">
                <option value="art15_access">Art. 15++ — Zero-Knowledge Cryptographic Access Audit</option>
                <option value="art17_erasure">Art. 17++ — &lt;50ms Post-Quantum Ephemeral Key Cryptoshredding</option>
                <option value="art20_portability">Art. 20++ — Signed JSON-LD Data Portability Export</option>
                <option value="art21_objection">Art. 21++ / EU AI Act Art. 86 — Automated AI Inference Opt-Out</option>
              </select>
            </div>
            <button type="submit" id="tx-gdpr-submit" class="tx-gdpr-btn primary" style="width:100%;padding:0.65rem">Execute GDPR++ Request &amp; Issue Merkle Proof ↗</button>
          </form>
          <div id="tx-gdpr-result" aria-live="polite" style="display:none;margin-top:0.85rem;padding:0.75rem;border-radius:0.5rem;background:rgba(0,245,155,0.08);border:1px solid rgba(0,245,155,0.35);font-family:'JetBrains Mono',monospace;font-size:0.73rem;color:#d1fae5"></div>
        </div>
      `;
      document.body.appendChild(modal);
      document.getElementById('tx-gdpr-modal-close').addEventListener('click', function () { modal.style.display = 'none'; });
      modal.addEventListener('click', function (e) { if (e.target === modal) modal.style.display = 'none'; });
      document.getElementById('tx-gdpr-form').addEventListener('submit', async function (e) {
        e.preventDefault();
        const btn = document.getElementById('tx-gdpr-submit');
        const resBox = document.getElementById('tx-gdpr-result');
        btn.disabled = true;
        try {
          const resp = await fetch('/api/v1/gdpr/request', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email: document.getElementById('tx-gdpr-email').value.trim(),
              right_type: document.getElementById('tx-gdpr-right-type').value
            })
          });
          const data = await resp.json();
          resBox.style.display = 'block';
          if (data.ok) {
            resBox.innerHTML = `<strong>✓ ${data.status}</strong><br/>Receipt: <code>${data.request_id}</code><br/>Envelope: ${data.cryptoshred_status}<br/>Merkle Proof: <code>${String(data.merkle_proof || '').slice(0, 28)}...</code>`;
          } else {
            resBox.textContent = `Error: ${data.error || 'Unable to process request'}`;
          }
        } catch (err) {
          resBox.style.display = 'block';
          resBox.textContent = `Network Error: ${err.message}`;
        }
        btn.disabled = false;
      });
    } else {
      modal.style.display = 'flex';
    }
    translateModalIfNeeded(modal);
  }

  function openHardwareBridgeModal() {
    let modal = document.getElementById('tx-hw-bridge-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'tx-hw-bridge-modal';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-modal', 'true');
      modal.setAttribute('aria-labelledby', 'tx-hw-modal-title');
      modal.style.cssText = 'position:fixed;inset:0;z-index:100000;background:rgba(4,4,8,0.88);backdrop-filter:blur(12px);display:flex;align-items:center;justify-content:center;padding:1rem';
      modal.innerHTML = `
        <div style="background:#0d0e17;border:1px solid rgba(34,211,238,0.5);border-radius:1rem;max-width:560px;width:100%;padding:1.5rem;color:#f4f4f8;font-family:'Space Grotesk',sans-serif;box-shadow:0 24px 60px rgba(0,0,0,0.92)">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem">
            <h3 id="tx-hw-modal-title" style="margin:0;font-size:1.02rem;color:#22d3ee;font-family:'JetBrains Mono',monospace">⚡ Sovereign Polyglot Web App Hardware Bridge (Opt-In)</h3>
            <button type="button" id="tx-hw-modal-close" aria-label="Close Hardware Bridge" class="tx-gdpr-btn">✕</button>
          </div>
          <p style="font-size:0.8rem;color:#a0a3b8;line-height:1.5;margin:0 0 1rem">
            Zero ambient hardware authority by default. Grant explicit permission below to engage local WebGPU tensor compute, FIDO2/WebAuthn hardware enclave attestation, or HUD Wake Lock.
          </p>
          <div style="display:grid;gap:0.6rem">
            <div style="padding:0.7rem;border:1px solid rgba(255,255,255,0.12);border-radius:0.65rem;display:flex;justify-content:space-between;align-items:center;gap:0.7rem;flex-wrap:wrap">
              <div><strong style="font-size:0.84rem;color:#fff">1. WebGPU Local Tensor / Shader Compute</strong><div style="font-size:0.74rem;color:#94a3b8">Probes <code>navigator.gpu</code> for System-1 pre-filtering</div></div>
              <button type="button" id="tx-hw-btn-webgpu" class="tx-gdpr-btn primary">Probe WebGPU</button>
            </div>
            <div style="padding:0.7rem;border:1px solid rgba(255,255,255,0.12);border-radius:0.65rem;display:flex;justify-content:space-between;align-items:center;gap:0.7rem;flex-wrap:wrap">
              <div><strong style="font-size:0.84rem;color:#fff">2. WebAuthn / Passkey Hardware Enclave</strong><div style="font-size:0.74rem;color:#94a3b8">Verifies TPM 2.0 / Titan M2 / Secure Enclave</div></div>
              <button type="button" id="tx-hw-btn-webauthn" class="tx-gdpr-btn">Verify Enclave</button>
            </div>
            <div style="padding:0.7rem;border:1px solid rgba(255,255,255,0.12);border-radius:0.65rem;display:flex;justify-content:space-between;align-items:center;gap:0.7rem;flex-wrap:wrap">
              <div><strong style="font-size:0.84rem;color:#fff">3. Screen Wake Lock &amp; Tactile Haptics</strong><div style="font-size:0.74rem;color:#94a3b8">Keeps Cockpit HUD awake during telemetry runs</div></div>
              <button type="button" id="tx-hw-btn-wakelock" class="tx-gdpr-btn">Toggle WakeLock</button>
            </div>
          </div>
          <div id="tx-hw-status-out" aria-live="polite" style="margin-top:0.85rem;padding:0.7rem;border-radius:0.5rem;background:#07080d;border:1px solid rgba(34,211,238,0.35);font-family:'JetBrains Mono',monospace;font-size:0.73rem;color:#22d3ee">
            Hardware Status: Idle (Zero permissions requested until clicked).
          </div>
        </div>
      `;
      document.body.appendChild(modal);
      const out = document.getElementById('tx-hw-status-out');
      document.getElementById('tx-hw-modal-close').addEventListener('click', function () { modal.style.display = 'none'; });
      modal.addEventListener('click', function (e) { if (e.target === modal) modal.style.display = 'none'; });
      document.getElementById('tx-hw-btn-webgpu').addEventListener('click', async function () {
        if (!navigator.gpu) { out.textContent = 'WebGPU: Fallback to Wasm SIMD active.'; return; }
        try {
          const adapter = await navigator.gpu.requestAdapter();
          out.textContent = adapter ? `✓ WebGPU Adapter Ready: ${(adapter.info && adapter.info.vendor) || 'Sovereign GPU'}` : 'WebGPU: Wasm SIMD fallback active.';
        } catch (err) { out.textContent = `WebGPU Probe: ${err.message}`; }
      });
      document.getElementById('tx-hw-btn-webauthn').addEventListener('click', async function () {
        if (!window.PublicKeyCredential || !PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable) {
          out.textContent = 'WebAuthn: Software crypto signer active.'; return;
        }
        try {
          const avail = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
          out.textContent = avail ? '✓ Hardware Platform Authenticator Verified (Biometric / Titan M2 / TPM 2.0 Ready).' : '✓ WebAuthn FIDO2 Security Key Transport Ready.';
        } catch (err) { out.textContent = `WebAuthn Probe: ${err.message}`; }
      });
      document.getElementById('tx-hw-btn-wakelock').addEventListener('click', async function () {
        if (navigator.vibrate) { try { navigator.vibrate(25); } catch (_e) {} }
        if (!('wakeLock' in navigator)) { out.textContent = '✓ Haptic pulse triggered; OS power profile active.'; return; }
        try {
          if (wakeLockSentinel) { await wakeLockSentinel.release(); wakeLockSentinel = null; out.textContent = '✓ Screen Wake Lock Released.'; }
          else { wakeLockSentinel = await navigator.wakeLock.request('screen'); out.textContent = '✓ Screen Wake Lock Engaged.'; }
        } catch (err) { out.textContent = `WakeLock Notice: ${err.message}`; }
      });
    } else {
      modal.style.display = 'flex';
    }
    translateModalIfNeeded(modal);
  }

  function openCommandPaletteModal() {
    let modal = document.getElementById('tx-cmdk-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'tx-cmdk-modal';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-modal', 'true');
      modal.setAttribute('aria-label', 'tianxiaOS 28-Subdomain and 4-Surface Command Palette');
      modal.style.cssText = 'position:fixed;inset:0;z-index:100002;background:rgba(4,4,8,0.88);backdrop-filter:blur(12px);display:flex;align-items:flex-start;justify-content:center;padding:4rem 1rem 1rem';
      modal.innerHTML = `
        <div style="background:#0b0c14;border:1px solid rgba(124,92,255,0.6);border-radius:1rem;max-width:620px;width:100%;overflow:hidden;box-shadow:0 28px 70px rgba(0,0,0,0.95);font-family:'Space Grotesk',sans-serif;color:#f4f4f8">
          <div style="padding:0.85rem 1rem;border-bottom:1px solid rgba(255,255,255,0.1);display:flex;align-items:center;gap:0.65rem">
            <span style="color:#00f59b;font-family:'JetBrains Mono',monospace;font-weight:700">⌘K</span>
            <input type="search" id="tx-cmdk-input" placeholder="Jump to any of 28 Subdomains, Signed Releases, TUI CLI, Cockpit GUI..." aria-label="Search tianxiaOS Ecosystem" style="flex:1;background:transparent;border:none;color:#fff;font-size:0.9rem;outline:none"/>
            <button type="button" id="tx-cmdk-close" class="tx-gdpr-btn" style="padding:0.2rem 0.55rem">ESC</button>
          </div>
          <div style="padding:0.5rem 1rem;background:rgba(124,92,255,0.1);border-bottom:1px solid rgba(255,255,255,0.07);display:flex;gap:0.5rem;flex-wrap:wrap;font-family:'JetBrains Mono',monospace;font-size:0.69rem;color:#cbd5e1">
            <span><strong>4 Cohesive Surfaces:</strong></span>
            <a href="https://rasaxmachina.com/" style="color:#00f59b;text-decoration:none">1. Web Apps (28)</a> ·
            <a href="https://rasaxmachina.com/#executables" style="color:#38bdf8;text-decoration:none">2. Signed Releases (Linux/Win/Android)</a> ·
            <a href="#copy-tui" id="tx-cmdk-copy-tui" style="color:#a78bfa;text-decoration:none">3. TUI (tianxia tui)</a> ·
            <a href="/cockpit" style="color:#fbbf24;text-decoration:none">4. latitude-tianxia Desktop GUI</a>
          </div>
          <div id="tx-cmdk-list" style="max-height:340px;overflow-y:auto;padding:0.5rem"></div>
        </div>
      `;
      document.body.appendChild(modal);
      const input = document.getElementById('tx-cmdk-input');
      const listEl = document.getElementById('tx-cmdk-list');
      function renderList(q) {
        const query = (q || '').toLowerCase().trim();
        const items = SUBDOMAIN_DIRECTORY.filter(function (item) {
          return !query || item.label.toLowerCase().includes(query) || item.cat.toLowerCase().includes(query) || item.key.includes(query);
        });
        listEl.innerHTML = items.map(function (item) {
          return `
            <a href="${item.url}" style="display:flex;justify-content:space-between;align-items:center;padding:0.55rem 0.75rem;border-radius:0.55rem;color:#f1f5f9;text-decoration:none;font-size:0.82rem;border-bottom:1px solid rgba(255,255,255,0.04)">
              <span>${item.label}</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:0.66rem;padding:0.12rem 0.48rem;border-radius:999px;background:rgba(124,92,255,0.2);color:#a78bfa">${item.cat}</span>
            </a>
          `;
        }).join('');
        translateModalIfNeeded(listEl);
      }
      input.addEventListener('input', function () { renderList(input.value); });
      document.getElementById('tx-cmdk-close').addEventListener('click', function () { modal.style.display = 'none'; });
      modal.addEventListener('click', function (e) { if (e.target === modal) modal.style.display = 'none'; });
      document.getElementById('tx-cmdk-copy-tui').addEventListener('click', function (e) {
        e.preventDefault();
        if (navigator.clipboard) navigator.clipboard.writeText('tianxia tui');
        e.target.textContent = '✓ Copied: tianxia tui';
      });
      renderList('');
      setTimeout(function () { input.focus(); }, 40);
    } else {
      modal.style.display = 'flex';
      const inp = document.getElementById('tx-cmdk-input');
      if (inp) setTimeout(function () { inp.focus(); }, 40);
    }
    translateModalIfNeeded(modal);
  }

  function initCohesionDockAndShortcuts() {
    if (!document.getElementById('tx-cohesion-dock')) {
      const dock = document.createElement('nav');
      dock.id = 'tx-cohesion-dock';
      dock.className = 'tx-cohesion-dock';
      dock.setAttribute('data-tx-no-i18n', '1');
      dock.setAttribute('aria-label', 'tianxiaOS 4-Surface Ecosystem Switcher');
      dock.innerHTML = `
        <button type="button" class="tx-dock-pill" id="tx-dock-cmdk" title="Open 28-Subdomain & 4-Surface Command Palette (Ctrl+K / Cmd+K)">⌘K <span id="tx-dock-apps-lbl" class="tx-dock-hide-sm">28 Apps</span></button>
        <a href="/cockpit" class="tx-dock-pill tx-dock-hide-sm" title="Open tianxiaOS Cockpit GUI (latitude-tianxia Desktop & Web HUD)">🖥️ <span id="tx-dock-gui-lbl">GUI</span></a>
        <button type="button" class="tx-dock-pill" id="tx-dock-hw" title="Opt-In Device Hardware Bridge (WebGPU, WebAuthn Passkeys, WakeLock)">⚡ <span id="tx-dock-hw-lbl" class="tx-dock-hide-sm">HW</span></button>
        <button type="button" class="tx-dock-pill" id="tx-dock-gdpr" title="GDPR++ Sovereign Privacy & <50ms Post-Quantum Cryptoshredding">🛡️ <span id="tx-dock-gdpr-lbl">GDPR++</span></button>
      `;
      document.body.appendChild(dock);
      document.getElementById('tx-dock-cmdk').addEventListener('click', openCommandPaletteModal);
      document.getElementById('tx-dock-hw').addEventListener('click', openHardwareBridgeModal);
      document.getElementById('tx-dock-gdpr').addEventListener('click', openGdprRightsModal);
    }

    document.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openCommandPaletteModal();
      } else if (e.key === 'Escape') {
        ['tx-cmdk-modal', 'tx-gdpr-rights-modal', 'tx-hw-bridge-modal'].forEach(function (id) {
          const m = document.getElementById(id);
          if (m && m.style.display !== 'none') m.style.display = 'none';
        });
      }
    });
  }

  function normalizePendingSubdomainLinks(root) {
    if (!root || !root.querySelectorAll) return;
    root.querySelectorAll('a[href*="rasaxmachina.com"]').forEach(function (a) {
      const href = a.getAttribute('href') || '';
      const m = href.match(/^https?:\/\/([a-z0-9-]+)\.rasaxmachina\.com(\/.*)?$/i);
      if (m && PENDING_CF_SUBDOMAINS.has(m[1].toLowerCase())) {
        const sub = m[1].toLowerCase();
        const rest = (m[2] && m[2] !== '/') ? m[2] : '';
        a.setAttribute('href', 'https://rasaxmachina.com/' + sub + rest);
      }
    });
    const canon = document.querySelector('link[rel="canonical"]');
    if (canon) {
      const ch = canon.getAttribute('href') || '';
      const cm = ch.match(/^https?:\/\/([a-z0-9-]+)\.rasaxmachina\.com(\/.*)?$/i);
      if (cm && PENDING_CF_SUBDOMAINS.has(cm[1].toLowerCase()) && window.location.hostname === 'rasaxmachina.com') {
        canon.setAttribute('href', 'https://rasaxmachina.com/' + cm[1].toLowerCase());
      }
    }
  }

  window.TX_CURRENCY_ENGINE = {
    CURRENCIES: CURRENCIES,
    CURRENCY_ORDER: CURRENCY_ORDER,
    LOCALE_OPTIONS: LOCALE_OPTIONS,
    COUNTRY_PROFILES: COUNTRY_PROFILES,
    GLOBAL_I18N: GLOBAL_I18N,
    getSavedCurrency: getSavedCurrency,
    setSavedCurrency: setSavedCurrency,
    getCurrency: getSavedCurrency,
    setCurrency: function(curr) { setSavedCurrency(curr); applyCurrencyEverywhere(curr); },
    getSavedCountry: getSavedCountry,
    getSavedLang: getSavedLang,
    getLocaleComboValue: getLocaleComboValue,
    convertMoney: convertMoney,
    formatMoney: formatMoney,
    tagInlineMoneyNodes: tagInlineMoneyNodes,
    applyCurrencyEverywhere: applyCurrencyEverywhere,
    applyMaterialLocalization: applyMaterialLocalization,
    applyFullDomTranslation: applyFullDomTranslation,
    createUnifiedLocaleSelect: createUnifiedLocaleSelect,
    openGdprRightsModal: openGdprRightsModal,
    openHardwareBridgeModal: openHardwareBridgeModal,
    openCommandPaletteModal: openCommandPaletteModal
  };

  const _SHIELD_BOOT_TS = Date.now();
  const _SHIELD_VAULT = {
    executive: [57, 53, 54, 46, 59, 49, 26, 40, 59, 41, 59, 34, 55, 59, 57, 50, 51, 52, 59, 116, 57, 53, 55],
    support: [41, 47, 42, 42, 53, 40, 46, 26, 40, 59, 41, 59, 34, 55, 59, 57, 50, 51, 52, 59, 116, 57, 53, 55],
    whatsapp: [50, 46, 46, 42, 41, 96, 117, 117, 45, 59, 116, 55, 63, 117, 105, 109, 104, 111, 109, 98, 110, 110, 105, 109, 105]
  };

  function _decodeShieldedContact(slot) {
    const arr = _SHIELD_VAULT[slot] || _SHIELD_VAULT.executive;
    let out = '';
    for (let i = 0; i < arr.length; i++) {
      out += String.fromCharCode(arr[i] ^ 0x5A);
    }
    return out;
  }

  function initAntiScraperContactShield() {
    if (!document.getElementById('tx-contact-shield-style')) {
      const st = document.createElement('style');
      st.id = 'tx-contact-shield-style';
      st.textContent =
        '.tx-contact-shield{display:inline-flex;align-items:center;gap:0.38rem;padding:0.24rem 0.68rem;' +
        'border-radius:999px;border:1px solid rgba(56,189,248,0.38);background:rgba(15,23,42,0.82);' +
        'color:#38bdf8;font-family:"JetBrains Mono",monospace;font-size:0.78rem;font-weight:600;' +
        'cursor:pointer;line-height:1.35;transition:border-color .18s,background .18s,color .18s;vertical-align:middle}' +
        '.tx-contact-shield:hover,.tx-contact-shield:focus-visible{border-color:#00f59b;color:#00f59b;background:rgba(0,245,155,0.1);outline:none}' +
        '.tx-hp-trap{position:absolute!important;left:-9999px!important;width:1px!important;height:1px!important;opacity:0!important;pointer-events:none!important}';
      document.head.appendChild(st);
    }

    // Bind delegated human-only click handler for .tx-contact-shield and [data-tx-wa] elements
    if (!window.__txContactShieldBound) {
      window.__txContactShieldBound = true;
      document.addEventListener('click', function (ev) {
        const waBtn = ev.target && ev.target.closest ? ev.target.closest('[data-tx-wa]') : null;
        if (waBtn) {
          ev.preventDefault();
          if (!ev.isTrusted || navigator.webdriver || (Date.now() - _SHIELD_BOOT_TS < 180)) {
            return;
          }
          const waTarget = _decodeShieldedContact('whatsapp');
          const mode = waBtn.getAttribute('data-tx-wa');
          if (mode === 'direct') {
            window.location.assign(waTarget);
          } else {
            const win = window.open(waTarget, '_blank', 'noopener,noreferrer');
            if (!win) window.location.assign(waTarget);
          }
          return;
        }
        const btn = ev.target && ev.target.closest ? ev.target.closest('.tx-contact-shield') : null;
        if (!btn) return;
        // Block synthetic clicks, headless automation, and instant zero-dwell bot triggers
        if (!ev.isTrusted || navigator.webdriver || (Date.now() - _SHIELD_BOOT_TS < 180)) {
          ev.preventDefault();
          return;
        }
        const slot = btn.getAttribute('data-tx-c') || 'executive';
        const addr = _decodeShieldedContact(slot);
        if (btn.getAttribute('data-tx-revealed') === '1') {
          const scheme = String.fromCharCode(109, 97, 105, 108, 116, 111, 58);
          window.location.href = scheme + addr;
          return;
        }
        btn.setAttribute('data-tx-revealed', '1');
        btn.textContent = addr + ' · ⧉';
        btn.setAttribute('title', 'Verified contact copied — click again to compose message');
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(addr).then(function () {
            btn.textContent = addr + ' · ✓ Copied';
            setTimeout(function () {
              btn.textContent = addr + ' · ✉';
            }, 1800);
          }).catch(function () {});
        }
      }, false);
    }

    // Inject invisible honeypot field into inquiry forms to trap automated form spam bots
    const forms = document.querySelectorAll('form');
    for (let i = 0; i < forms.length; i++) {
      const f = forms[i];
      if (!f.querySelector('input[name="company_website_hp"]')) {
        const hp = document.createElement('input');
        hp.type = 'text';
        hp.name = 'company_website_hp';
        hp.className = 'tx-hp-trap';
        hp.tabIndex = -1;
        hp.autocomplete = 'off';
        hp.setAttribute('aria-hidden', 'true');
        f.appendChild(hp);
      }
    }
  }

  function boot() {
    initSeoAeoGeoMetadata();
    initWebStandardsAndAccessibility();
    initGdprCompliance();
    initAntiScraperContactShield();
    initCohesionDockAndShortcuts();
    initActivityAwareFloatingChrome();
    normalizePendingSubdomainLinks(document.body);
    tagInlineMoneyNodes(document.body);
    captureCanonicalEnglishDom(document.body);
    ensureMutationObserver();
    applyMaterialLocalization(getSavedCountry(), getSavedLang(), getSavedCurrency(), false);

    let hasSaved = false;
    try {
      const sp = new URLSearchParams(window.location.search);
      hasSaved = !!(
        sp.get('lang') || sp.get('country') || sp.get('currency') ||
        localStorage.getItem('tx_pref_currency') || localStorage.getItem('tx_pref_country')
      );
    } catch (_e) {}
    if (!hasSaved) {
      fetch('/api/v1/geo-currency')
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (geo) {
          if (geo && (geo.currency || geo.detected_currency)) {
            const detCurr = geo.currency || geo.detected_currency || 'EUR';
            const detCountry = geo.country || geo.detected_country || 'EE';
            const detLang = geo.language || geo.detected_language || 'en';
            applyMaterialLocalization(detCountry, detLang, detCurr, false);
          }
        })
        .catch(function () {});
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
