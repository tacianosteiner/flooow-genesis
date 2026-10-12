# FLOOOW — Global Signal Source Catalog

Status: RESEARCH_AUTHORIZED. Observed: 2026-10-11. Implementation, procurement and production integration authority: NONE.

## Reading contract

Each entry below is a complete record. Source URLs point to the claim register; follow evidence IDs for direct primary links. `OBSERVED` means documentation was read, not that the underlying product data was collected. `INDEPENDENTLY_REPRODUCED=NO` applies to every entry. All entries inherit: `CLAIM_VERSION=PUBLIC_PAGE_OBSERVED_2026-10-11`; `CLAIM_DATE=per evidence row, otherwise UNKNOWN`; `CURRENTNESS=documentation reviewed on observation date, product delivery not tested`; `LICENSE_NOTES=public readability grants no collection, redistribution, training or commercial reuse license; exact dataset rights UNKNOWN`; `ROBOTS_OR_ACCESS_NOTES=no crawler/API/account access performed; robots, rate limits and bulk collection permission UNKNOWN`; `PROVENANCE_SCORE_INPUTS=source identity, URL, publication/observation date, method, coverage, consent, revision, raw lineage and independent validation; no numeric score assigned`. These inherited fields apply separately to every source, including government data; open-data labeling still requires precise license review.

How early remains UNTESTED for all sources. EARLY/INTERMEDIATE labels below are hypotheses from the temporal model. Authentic first-party documentation about a vendor's estimator is not first-party shopper data. Level is attached to a particular record/method, never blanket vendor trust. Capabilities listed are documented or hypothesized, with evidence and qualifications; they are not production endorsements.

## SW — Similarweb Retail / Shopper Intelligence

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | SW / Similarweb Retail / Shopper Intelligence |
| SOURCE_OWNER | Similarweb |
| SOURCE_URL / CLAIM | [E01](https://www.similarweb.com/corp/retail/shopper-insights/); [E02](https://www.similarweb.com/corp/retail/shopper-insights/); [E03](https://support.similarweb.com/hc/en-us/articles/33639235837981-Retail-Intelligence-Metrics); [E04](https://support.similarweb.com/hc/en-us/articles/33639235837981-Retail-Intelligence-Metrics); [E05](https://docs.similarweb.com/api-v5/similarweb-api); [E06](https://support.similarweb.com/hc/en-us/articles/35907041527965-Retail-Intelligence-with-AI-MCP-AI-Studio); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Global claimed 70+ countries; exact metric-by-country coverage UNKNOWN |
| SOURCE_TYPE | L2 catalog observations / L3 behavior and sales estimates |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; SHOPPER_INTELLIGENCE; PRODUCT_INTELLIGENCE; DIGITAL_SHELF_INTELLIGENCE; PRICE_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; CHANNEL_MEASUREMENT; ADVERTISING_INTELLIGENCE; COMPETITIVE_INTELLIGENCE; EMERGING_COMMERCE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Account/paid entitlement for intelligence; exact price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L2 catalog observations / L3 behavior and sales estimates; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | SKU/product, keyword, category, brand, retailer; matching quality UNKNOWN |
| UPDATE_FREQUENCY | Weekly retail, weekly/monthly Amazon; nine-day documented lag; custom feed cadence UNKNOWN |
| HISTORICAL_DEPTH | Generic API up to seven years claimed; per-retail dataset history UNKNOWN |
| API | YES documented API; endpoint entitlement/quota UNKNOWN |
| DATA_FEED | YES advertised feeds/Data Hub |
| EXPORT | Integration advertised; exact export license UNKNOWN |
| MCP_IF_ANY | YES documented |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Account/paid entitlement for intelligence; exact price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Traffic/search may rise while purchases fall; missing app/offline population; feed delivery vs event-time lag |
| FLOOOW_RELEVANCE | Outside-in consideration signals complement purchase records; require web/app coverage and estimator calibration |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; Outside-in consideration signals complement purchase records; require web/app coverage and estimator calibration; no provider selected |

## ATLAS — Stackline Atlas

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | ATLAS / Stackline Atlas |
| SOURCE_OWNER | Stackline |
| SOURCE_URL / CLAIM | [E07](https://www.stackline.com/atlas); [E08](https://www.stackline.com/atlas); [E10](https://www.stackline.com/releases/2024-winter-release); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | 26 countries claimed; exact countries/retailers per metric UNKNOWN |
| SOURCE_TYPE | L3 market intelligence; observation/estimation mix UNKNOWN |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; SHOPPER_INTELLIGENCE; PRODUCT_INTELLIGENCE; DIGITAL_SHELF_INTELLIGENCE; PRICE_INTELLIGENCE; CHANNEL_MEASUREMENT; ADVERTISING_INTELLIGENCE; COMPETITIVE_INTELLIGENCE; EMERGING_COMMERCE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Demo/account; commercial terms and price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L3 market intelligence; observation/estimation mix UNKNOWN; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | SKU, keyword, brand, category; variant matching UNKNOWN |
| UPDATE_FREQUENCY | Daily measurement claim; weekly share updates; per-field latency UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | YES Segment API announced; current schema/rate/rights UNKNOWN |
| DATA_FEED | Snowflake sharing announced |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Demo/account; commercial terms and price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Accuracy denominator UNKNOWN; daily/weekly/real-time wording not one SLA |
| FLOOOW_RELEVANCE | Compare category-wide outside-in signals; 97% claim cannot define confidence |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; Compare category-wide outside-in signals; 97% claim cannot define confidence; no provider selected |

## BEACON — Stackline Beacon

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | BEACON / Stackline Beacon |
| SOURCE_OWNER | Stackline |
| SOURCE_URL / CLAIM | [E09](https://www.stackline.com/beacon); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Amazon/Walmart and other retailers advertised; country roster UNKNOWN |
| SOURCE_TYPE | Brand-authorized operational data plus vendor forecasts; L0 only for reconciled owned records, otherwise L3 |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; SHOPPER_INTELLIGENCE; PRODUCT_INTELLIGENCE; DIGITAL_SHELF_INTELLIGENCE; PRICE_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; CHANNEL_MEASUREMENT; PURCHASE_VERIFICATION; ADVERTISING_INTELLIGENCE; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Brand account/data authorization; price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | Brand-authorized operational data plus vendor forecasts; L0 only for reconciled owned records, otherwise L3; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Brand SKU/keyword/performance; SKU-level forecasts |
| UPDATE_FREQUENCY | Real-time sales claim; measured delivery latency UNKNOWN |
| HISTORICAL_DEPTH | 52-week forecast horizon is not historical depth; history UNKNOWN |
| API | UNKNOWN; do not substitute unrelated beacon.com API |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Brand account/data authorization; price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Forecast ≠ actual; brand permissions do not authorize competitor purchase records |
| FLOOOW_RELEVANCE | Inside-out brand performance comparator to Atlas; operational truth still requires reconciliation |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; Inside-out brand performance comparator to Atlas; operational truth still requires reconciliation; no provider selected |

## NIQ — NIQ Commerce Intelligence / Commerce Lab

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | NIQ / NIQ Commerce Intelligence / Commerce Lab |
| SOURCE_OWNER | NielsenIQ |
| SOURCE_URL / CLAIM | [E11](https://nielseniq.com/global/en/news-center/2026/niq-launches-commerce-lab-to-build-the-data-and-measurement-layer-for-ai-driven-commerce/); [E12](https://nielseniq.com/global/en/client-learning/retail-measurement-services/retail-measurement-process/); [E13](https://nielseniq.com/global/en/insights/analysis/2022/pos-data-vs-panel-data-key-differences/); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Global product/market coverage UNKNOWN by dataset |
| SOURCE_TYPE | L3 projected RMS/panels; transaction inputs retain original provenance |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; SHOPPER_INTELLIGENCE; PRODUCT_INTELLIGENCE; PRICE_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; CHANNEL_MEASUREMENT; PURCHASE_VERIFICATION; ADVERTISING_INTELLIGENCE; COMPETITIVE_INTELLIGENCE; EMERGING_COMMERCE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Commercial client/panel-specific rights; exact price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L3 projected RMS/panels; transaction inputs retain original provenance; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Store/POS and household/purchase concepts; market/product taxonomy specific |
| UPDATE_FREQUENCY | UNKNOWN by service |
| HISTORICAL_DEPTH | UNKNOWN by service |
| API | UNKNOWN for Commerce Lab; announced concepts not endpoints |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Commercial client/panel-specific rights; exact price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Panel reporting/projection error, retailer exclusions and identity linkage unverified |
| FLOOOW_RELEVANCE | Separate POS movement, panel behavior and agentic program design |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; Separate POS movement, panel behavior and agentic program design; no provider selected |

## PROF — Profitero / Profitero+

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | PROF / Profitero / Profitero+ |
| SOURCE_OWNER | Profitero |
| SOURCE_URL / CLAIM | [E14](https://www.profitero.com/); [E15](https://www.profitero.com/product/digital-shelf); [E16](https://www.profitero.com/open-commerce-ecosystem); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | 70+ countries and 1,400+ retailers claimed; specific coverage UNKNOWN |
| SOURCE_TYPE | L2 shelf observations / L3 Amazon sales estimates |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; PRODUCT_INTELLIGENCE; DIGITAL_SHELF_INTELLIGENCE; PRICE_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; CHANNEL_MEASUREMENT; ADVERTISING_INTELLIGENCE; COMPETITIVE_INTELLIGENCE; EMERGING_COMMERCE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Commercial app login/demo; exact price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L2 shelf observations / L3 Amazon sales estimates; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | SKU/product fields, retailer, keyword placement, review/content |
| UPDATE_FREQUENCY | Daily claimed; delivery latency UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | UNKNOWN public self-service API |
| DATA_FEED | Snowflake and partner delivery advertised |
| EXPORT | UNKNOWN entitlement |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Commercial app login/demo; exact price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Observed listing/stock ≠ verified inventory or purchase; estimates not actual |
| FLOOOW_RELEVANCE | SPECIALIST_SOURCE role: shelf execution/launch/price complements behavior/POS; not foundational truth |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | SPECIALIST_BENCHMARK; SPECIALIST_SOURCE role: shelf execution/launch/price complements behavior/POS; not foundational truth; no provider selected |

## TCC — TikTok Creative Center

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | TCC / TikTok Creative Center |
| SOURCE_OWNER | TikTok |
| SOURCE_URL / CLAIM | [E17](https://ads.tiktok.com/resources/help/article/creative-center?redirected=2); [E18](https://ads-useast2a.tiktok.com/resources/help/article/how-to-use-the-top-ads-dashboard); [E19](https://ads.tiktok.com/help/article/how-to-use-top-products?lang=id); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Region filters; per-feature available regions UNKNOWN |
| SOURCE_TYPE | L1 platform-curated ad/trend signals, not census |
| SIGNAL_FAMILIES | ADVERTISING_INTELLIGENCE; ATTENTION_INTELLIGENCE; CREATOR_INTELLIGENCE; PRODUCT_INTELLIGENCE; DEMAND_INTELLIGENCE; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Public resource; login visible for deeper interfaces; per-feature auth UNKNOWN; no paid plan used |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L1 platform-curated ad/trend signals, not census; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Ad creative, keyword, creator, product/category; filter-relative metrics |
| UPDATE_FREQUENCY | Time-window filters; refresh SLA UNKNOWN |
| HISTORICAL_DEPTH | Selectable periods; retained depth UNKNOWN |
| API | UNKNOWN for Creative Center trend dataset |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Public resource; login visible for deeper interfaces; per-feature auth UNKNOWN; no paid plan used; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Curated winning ads create selection/survivorship bias; top products are ad-popular |
| FLOOOW_RELEVANCE | Early attention/ad hypothesis source; separate search intent and conversions |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; Early attention/ad hypothesis source; separate search intent and conversions; no provider selected |

## TONE — TikTok One Creative Suite

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | TONE / TikTok One Creative Suite |
| SOURCE_OWNER | TikTok |
| SOURCE_URL / CLAIM | [E20](https://ads.us.tiktok.com/help/article/tiktok-one-brand-and-creator-agreement?lang=en); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Service markets UNKNOWN |
| SOURCE_TYPE | L1 authorized creative workflow; output not universal signal |
| SIGNAL_FAMILIES | ADVERTISING_INTELLIGENCE; ATTENTION_INTELLIGENCE; CREATOR_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Contractual brand/creator access; costs UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L1 authorized creative workflow; output not universal signal; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Brand/creator/campaign service objects |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | UNKNOWN for benchmark data |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Contractual brand/creator access; costs UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Creator campaign participation ≠ population velocity |
| FLOOOW_RELEVANCE | Creator workflow context; public Creative Center is distinct |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | SPECIALIST_BENCHMARK; Creator workflow context; public Creative Center is distinct; no provider selected |

## META — Meta Ad Library

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | META / Meta Ad Library |
| SOURCE_OWNER | Meta |
| SOURCE_URL / CLAIM | [E21](https://br-fr.facebook.com/ads/library/api/?source=onboarding); [E22](https://br-fr.facebook.com/ads/library/api/?source=onboarding); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | UI active ads across Meta; API global political/issue, UK/EU any type |
| SOURCE_TYPE | L1 ad-delivery records with estimated/ranged measures |
| SIGNAL_FAMILIES | ADVERTISING_INTELLIGENCE; ATTENTION_INTELLIGENCE; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Public search; API verified account/developer/app; price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L1 ad-delivery records with estimated/ranged measures; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Ad ID, advertiser/Page, creative, delivery dates; scoped reach |
| UPDATE_FREQUENCY | Current delivery state; update delay UNKNOWN |
| HISTORICAL_DEPTH | API: seven years political/issue; one year UK/EU any-type; other commercial history not general API scope |
| API | YES scoped Ad Library API; identity/app/account requirements |
| DATA_FEED | UNKNOWN |
| EXPORT | API responses; bulk archival redistribution license UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Public search; API verified account/developer/app; price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Brazil ordinary commercial UI availability does not grant API archive; reach is estimated |
| FLOOOW_RELEVANCE | Advertising activity comparator; no universal conversion/spend truth |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; Advertising activity comparator; no universal conversion/spend truth; no provider selected |

## GADS — Google Ads Transparency Center

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | GADS / Google Ads Transparency Center |
| SOURCE_OWNER | Google |
| SOURCE_URL / CLAIM | [E23](https://support.google.com/My-Ad-Center-Help/answer/12155361?hl=en); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Serving-region filters; complete market/archive scope UNKNOWN |
| SOURCE_TYPE | L1 advertising transparency |
| SIGNAL_FAMILIES | ADVERTISING_INTELLIGENCE; ATTENTION_INTELLIGENCE; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Public lookup described; exact limits/auth UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L1 advertising transparency; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Advertiser/domain, creative, region/date |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN by jurisdiction/ad type |
| API | UNKNOWN supported public general API; Google Ads API is distinct |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Public lookup described; exact limits/auth UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Identity verification ≠ product legitimacy/performance |
| FLOOOW_RELEVANCE | Advertiser presence and creative change; not commercial conversion |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; Advertiser presence and creative change; not commercial conversion; no provider selected |

## GT — Google Trends

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | GT / Google Trends |
| SOURCE_OWNER | Google |
| SOURCE_URL / CLAIM | [E24](https://support.google.com/trends/answer/4365533?hl=en); [E25](https://support.google.com/trends/answer/4365533?hl=en); [E26](https://developers.google.com/search/apis/trends); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Countries/subregions; low-volume coverage censored |
| SOURCE_TYPE | L1 sampled search interest |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; ATTENTION_INTELLIGENCE; PRODUCT_INTELLIGENCE; EMERGING_COMMERCE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Public UI; alpha application/acceptance needed; price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L1 sampled search interest; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Term/topic, geography, time bucket; relative index |
| UPDATE_FREQUENCY | Window-dependent aggregation; not continuous population measure |
| HISTORICAL_DEPTH | API alpha rolling five years; UI history by query UNKNOWN here |
| API | YES limited alpha; not general public entitlement |
| DATA_FEED | UNKNOWN |
| EXPORT | UI export entitlement UNKNOWN in reviewed pages |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Public UI; alpha application/acceptance needed; price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Noise and suppressed values; changing normalization can create apparent acceleration |
| FLOOOW_RELEVANCE | SEARCH_INTENT precursor test; normalize query/topic/calendar context |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; SEARCH_INTENT precursor test; normalize query/topic/calendar context; no provider selected |

## MERCH — Google Shopping / Merchant ecosystem

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | MERCH / Google Shopping / Merchant ecosystem |
| SOURCE_OWNER | Google |
| SOURCE_URL / CLAIM | [E27](https://developers.google.com/merchant/api/reference/rest); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Account/market-specific; public shopping not a global census |
| SOURCE_TYPE | L1 authorized merchant inputs / L2 visible listing |
| SIGNAL_FAMILIES | PRODUCT_INTELLIGENCE; DIGITAL_SHELF_INTELLIGENCE; PRICE_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Authorized merchant account for API; price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L1 authorized merchant inputs / L2 visible listing; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Account, product input, product attributes; seller-scoped |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | YES Merchant API, authorized accounts; quotas UNKNOWN |
| DATA_FEED | Merchant product-management feeds distinct from market-data feed |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Authorized merchant account for API; price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Submitted price/availability can differ from checkout/fulfillment |
| FLOOOW_RELEVANCE | Compare permitted listing attributes; no competitor order rights |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | SPECIALIST_BENCHMARK; Compare permitted listing attributes; no competitor order rights; no provider selected |

## PIN — Pinterest Trends

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | PIN / Pinterest Trends |
| SOURCE_OWNER | Pinterest |
| SOURCE_URL / CLAIM | [E28](https://help.pinterest.com/en/business/article/pinterest-trends); [E29](https://developer.pinterest.com/docs/analytics-and-reports/analytics-overview/); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Regional features/testing; full feature-country list UNKNOWN |
| SOURCE_TYPE | L1 normalized search/save/shopping interests |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; ATTENTION_INTELLIGENCE; CREATOR_INTELLIGENCE; PRODUCT_INTELLIGENCE; EMERGING_COMMERCE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Business login for advertiser features; paid requirement UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L1 normalized search/save/shopping interests; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Keyword/category/region; demographic features |
| UPDATE_FREQUENCY | Weekly/monthly/yearly changes shown; refresh SLA UNKNOWN |
| HISTORICAL_DEPTH | Up to two years documented; feature-specific scope |
| API | Trend analytics mentioned; exact endpoint/entitlement UNKNOWN |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Business login for advertiser features; paid requirement UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Per-term normalization and regional audience bias; predictions ≠ actual |
| FLOOOW_RELEVANCE | Planning/aspiration signals; test whether saves precede purchase |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; Planning/aspiration signals; test whether saves precede purchase; no provider selected |

## YT — YouTube public discovery / Data API

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | YT / YouTube public discovery / Data API |
| SOURCE_OWNER | Google / YouTube |
| SOURCE_URL / CLAIM | [E30](https://developers.google.com/youtube/v3/docs/videos/list); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | mostPopular scoped to content region/category; coverage completeness UNKNOWN |
| SOURCE_TYPE | L1 platform popularity / L4 creator product mentions / L5 extracted inference |
| SIGNAL_FAMILIES | ATTENTION_INTELLIGENCE; CREATOR_INTELLIGENCE; PRODUCT_INTELLIGENCE; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Public videos; API project credentials; paid requirement UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L1 platform popularity / L4 creator product mentions / L5 extracted inference; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Video/channel, region/category; mentions need adjudicated extraction |
| UPDATE_FREQUENCY | Current API chart; refresh SLA UNKNOWN |
| HISTORICAL_DEPTH | Historical chart retention UNKNOWN; metadata dates ≠ historical chart |
| API | YES Data API; API key/auth/quota per operation must be verified |
| DATA_FEED | UNKNOWN |
| EXPORT | API output under developer policies; redistribution UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Public videos; API project credentials; paid requirement UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Views ≠ unique buyers; content region ≠ viewer residency or product origin |
| FLOOOW_RELEVANCE | Creator/product mention discovery; measure popularity sampling bias |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; Creator/product mention discovery; measure popularity sampling bias; no provider selected |

## C1688 — 1688

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | C1688 / 1688 |
| SOURCE_OWNER | Alibaba Group |
| SOURCE_URL / CLAIM | [E31](https://www.alibabagroup.com/en-US/about-alibaba-businesses-1941299332078632960); [E49](https://open.1688.com/); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | China wholesale role; foreign researcher access UNKNOWN |
| SOURCE_TYPE | L2 listings / L1 authorized seller records / L5 supplier-density inference |
| SIGNAL_FAMILIES | SUPPLY_INTELLIGENCE; PRODUCT_INTELLIGENCE; PRICE_INTELLIGENCE; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Login, China phone, business account: UNKNOWN by function |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L2 listings / L1 authorized seller records / L5 supplier-density inference; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Candidate supplier/listing/variant; API granularity UNKNOWN |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | UNKNOWN current verified scope; portal fetch failed |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Login, China phone, business account: UNKNOWN by function; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Seller count ≠ factory count; quote ≠ transactable landed price |
| FLOOOW_RELEVANCE | Wholesale role supported; supplier-density lead hypothesis requires licensed longitudinal sample |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | INSUFFICIENT_EVIDENCE; Wholesale role supported; supplier-density lead hypothesis requires licensed longitudinal sample; no provider selected |

## TAO — Taobao

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | TAO / Taobao |
| SOURCE_OWNER | Alibaba Group |
| SOURCE_URL / CLAIM | [E32](https://home.alibabagroup.com/en-US/document-1796329702713982976); [E49](https://open.1688.com/); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | China; research coverage UNKNOWN |
| SOURCE_TYPE | L2 retail listings / L1 authorized transactions / L5 traction inference |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; SHOPPER_INTELLIGENCE; PRODUCT_INTELLIGENCE; DIGITAL_SHELF_INTELLIGENCE; PRICE_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; CHANNEL_MEASUREMENT; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Login/China phone/business requirements UNKNOWN by function |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L2 retail listings / L1 authorized transactions / L5 traction inference; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Candidate listing/category/brand; API scope UNKNOWN |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | UNKNOWN verified open.taobao.com scope; failed public fetch |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Login/China phone/business requirements UNKNOWN by function; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Visible counters/ranks ≠ GMV; duplicate/variant identities |
| FLOOOW_RELEVANCE | Separate Taobao assortment/demand hypotheses from Tmall |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | INSUFFICIENT_EVIDENCE; Separate Taobao assortment/demand hypotheses from Tmall; no provider selected |

## TMALL — Tmall

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | TMALL / Tmall |
| SOURCE_OWNER | Alibaba Group |
| SOURCE_URL / CLAIM | [E32](https://home.alibabagroup.com/en-US/document-1796329702713982976); [E49](https://open.1688.com/); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | China; research coverage UNKNOWN |
| SOURCE_TYPE | L2 brand/catalog listings / L1 authorized transactions |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; SHOPPER_INTELLIGENCE; PRODUCT_INTELLIGENCE; DIGITAL_SHELF_INTELLIGENCE; PRICE_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; CHANNEL_MEASUREMENT; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Login/China phone/business requirements UNKNOWN by function |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L2 brand/catalog listings / L1 authorized transactions; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Candidate brand/product/category; scope UNKNOWN |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | UNKNOWN verified shared ecosystem API scope |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Login/China phone/business requirements UNKNOWN by function; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Brand listing presence ≠ verified launch time or retention |
| FLOOOW_RELEVANCE | Brand traction/launch hypothesis; separate platform sampling |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | INSUFFICIENT_EVIDENCE; Brand traction/launch hypothesis; separate platform sampling; no provider selected |

## JD — JD / JD commerce

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | JD / JD / JD commerce |
| SOURCE_OWNER | JD.com |
| SOURCE_URL / CLAIM | [E33](https://jos.jd.com/api/list.htm?id=117); [E34](https://opendj.jd.com/index.html); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | China retail/instant delivery; market scope UNKNOWN |
| SOURCE_TYPE | L1 permitted platform records / L2 listings |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; PRODUCT_INTELLIGENCE; DIGITAL_SHELF_INTELLIGENCE; PRICE_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; CHANNEL_MEASUREMENT; PURCHASE_VERIFICATION; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Operational credentials/rights must be checked; China phone/business UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L1 permitted platform records / L2 listings; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | API families listed; specific data granularity UNKNOWN |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | YES developer platform listed; research scope/rights UNKNOWN |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Operational credentials/rights must be checked; China phone/business UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Legacy platform migration; platform-reported commerce not independent transaction verification |
| FLOOOW_RELEVANCE | Purchase/launch/category acceleration hypotheses; no verified dataset collected |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | INSUFFICIENT_EVIDENCE; Purchase/launch/category acceleration hypotheses; no verified dataset collected; no provider selected |

## DOU — Douyin / Douyin Ecommerce

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | DOU / Douyin / Douyin Ecommerce |
| SOURCE_OWNER | Douyin platform; exact contractual entity UNKNOWN |
| SOURCE_URL / CLAIM | [E35](https://open.douyin.com/platform/resource/docs/accession-guide/platform-introduction/); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | China; API country/app eligibility UNKNOWN |
| SOURCE_TYPE | L1 authorized platform data / L4 public content / L5 velocity inference |
| SIGNAL_FAMILIES | ATTENTION_INTELLIGENCE; CREATOR_INTELLIGENCE; ADVERTISING_INTELLIGENCE; PRODUCT_INTELLIGENCE; CHANNEL_MEASUREMENT; SHOPPER_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Authorization documented; China phone/business requirements UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L1 authorized platform data / L4 public content / L5 velocity inference; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Video/user/statistics/vertical capabilities; commerce history UNKNOWN |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | YES authorized platform capabilities; unrestricted commerce API NO evidence |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Authorization documented; China phone/business requirements UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Authorized creator stats ≠ rival storefront sales or market census |
| FLOOOW_RELEVANCE | Content-to-commerce/live-commerce hypothesis distinct from TikTok |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | INSUFFICIENT_EVIDENCE; Content-to-commerce/live-commerce hypothesis distinct from TikTok; no provider selected |

## XHS — Xiaohongshu

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | XHS / Xiaohongshu |
| SOURCE_OWNER | Xiaohongshu; exact contractual entity UNKNOWN |
| SOURCE_URL / CLAIM | [E36](https://open.xiaohongshu.com/); [E37](https://openaccount.xiaohongshu.com/docs/quick-start); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | China; international feature access UNKNOWN |
| SOURCE_TYPE | L4 discovery/community / L1 authorized account or merchant data |
| SIGNAL_FAMILIES | ATTENTION_INTELLIGENCE; CREATOR_INTELLIGENCE; PRODUCT_INTELLIGENCE; DEMAND_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Authorization for account API; commerce/phone/business requirements UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L4 discovery/community / L1 authorized account or merchant data; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Authorized user identity documented; community/product trend granularity UNKNOWN |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | Account authorization documented; commerce portal indexed; research API UNKNOWN |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Authorization for account API; commerce/phone/business requirements UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Portal timeout not proof of regional block; saved content ≠ purchase intent verified |
| FLOOOW_RELEVANCE | Aspiration/lifestyle emergence hypothesis; separate merchant and community access |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | INSUFFICIENT_EVIDENCE; Aspiration/lifestyle emergence hypothesis; separate merchant and community access; no provider selected |

## PDD — Pinduoduo

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | PDD / Pinduoduo |
| SOURCE_OWNER | PDD Holdings; service entity per agreement UNKNOWN |
| SOURCE_URL / CLAIM | [E38](https://open.yangkeduo.com/application/home); [E39](https://www.sec.gov/Archives/edgar/data/1737806/000110465926050727/pdd-20251231x20f.htm); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | China platform distinct from international Temu |
| SOURCE_TYPE | L2 listing / L1 authorized merchant data / L3 corporate aggregates |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; PRODUCT_INTELLIGENCE; PRICE_INTELLIGENCE; CHANNEL_MEASUREMENT; SHOPPER_INTELLIGENCE; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Function-specific login/phone/business requirements UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L2 listing / L1 authorized merchant data / L3 corporate aggregates; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | API portal and corporate report; product/category data scope UNKNOWN |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | Corporate history not SKU history; SKU history UNKNOWN |
| API | YES portal/API docs listed; current anonymous research API UNKNOWN |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Function-specific login/phone/business requirements UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Price elasticity cannot be inferred from discount listings alone |
| FLOOOW_RELEVANCE | Value/mass-demand/elasticity hypotheses need denominator and transactions |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | INSUFFICIENT_EVIDENCE; Value/mass-demand/elasticity hypotheses need denominator and transactions; no provider selected |

## TEMU — Temu

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | TEMU / Temu |
| SOURCE_OWNER | PDD Holdings; regional partner entity per terms |
| SOURCE_URL / CLAIM | [E39](https://www.sec.gov/Archives/edgar/data/1737806/000110465926050727/pdd-20251231x20f.htm); [E40](https://partner.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=8fb9a7179af64071a5a443b805fe3484); [E41](https://partner.temu.com/protocol/temu_partner_platform_terms_20250523.pdf); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Regional partner platforms; cross-border origin not established per listing |
| SOURCE_TYPE | L2 listings / L1 seller-authorized operations / L3 corporate aggregate |
| SIGNAL_FAMILIES | SUPPLY_INTELLIGENCE; PRODUCT_INTELLIGENCE; PRICE_INTELLIGENCE; DIGITAL_SHELF_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; TRADE_INTELLIGENCE; COMPETITIVE_INTELLIGENCE; EMERGING_COMMERCE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Partner/seller authorization; China phone UNKNOWN; permitted business roles in terms |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L2 listings / L1 seller-authorized operations / L3 corporate aggregate; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Seller/shop management APIs; exact research field scope UNKNOWN |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | YES partner APIs; seller authorization for non-public shop management |
| DATA_FEED | UNKNOWN |
| EXPORT | Operational response not blanket research/export right |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Partner/seller authorization; China phone UNKNOWN; permitted business roles in terms; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Temu listing ≠ China origin; seller-managed feeds not global market history |
| FLOOOW_RELEVANCE | Cross-border diffusion hypothesis; origin requires manufacturer/trade evidence |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | SPECIALIST_BENCHMARK; Cross-border diffusion hypothesis; origin requires manufacturer/trade evidence; no provider selected |

## DW — DataWeave

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | DW / DataWeave |
| SOURCE_OWNER | DataWeave |
| SOURCE_URL / CLAIM | [E42](https://dataweave.com/blog/fueling-agentic-commerce-introducing-the-dataweave-data-collection-api); [E43](https://dataweave.com/blog/own-your-product-matches-gain-the-power-of-accuracy-and-control-at-your-fingertips); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Cross-retailer/region claims; exact roster UNKNOWN |
| SOURCE_TYPE | L2 collected shelf observations / L3 analytics |
| SIGNAL_FAMILIES | PRODUCT_INTELLIGENCE; DIGITAL_SHELF_INTELLIGENCE; PRICE_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; COMPETITIVE_INTELLIGENCE; EMERGING_COMMERCE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Commercial entitlement; exact price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L2 collected shelf observations / L3 analytics; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Product/retailer matching advertised; audited matches not observed |
| UPDATE_FREQUENCY | On-demand collection API advertised; SLA UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | YES advertised Data Collection API; rights/rates UNKNOWN |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Commercial entitlement; exact price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Matching claims cannot establish canonical product identity |
| FLOOOW_RELEVANCE | Material challenger to shelf/access/matching role; superiority unproven |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | SPECIALIST_BENCHMARK; Material challenger to shelf/access/matching role; superiority unproven; no provider selected |

## MIK — MikMak

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | MIK / MikMak |
| SOURCE_OWNER | MikMak |
| SOURCE_URL / CLAIM | [E44](https://www.mikmak.com/product-updates); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Supported US/Canada inventory release; other precise scope UNKNOWN |
| SOURCE_TYPE | Authorized commerce/media data + integrated third-party POS |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; SHOPPER_INTELLIGENCE; PRODUCT_INTELLIGENCE; AVAILABILITY_INTELLIGENCE; CHANNEL_MEASUREMENT; PURCHASE_VERIFICATION; ADVERTISING_INTELLIGENCE; COMPETITIVE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Brand/client entitlement; exact price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | Authorized commerce/media data + integrated third-party POS; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Retailer/media/commerce measures; SKU scope UNKNOWN |
| UPDATE_FREQUENCY | Daily US/Canada inventory refresh claimed; other SLAs UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | UNKNOWN |
| DATA_FEED | SPINS POS integration advertised; portable feed rights UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Brand/client entitlement; exact price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Click/purchase-intent vs matched purchase; attribution identity and selection bias |
| FLOOOW_RELEVANCE | Material media→commerce/POS challenger; no unmeasured attribution causal claim |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | SPECIALIST_BENCHMARK; Material media→commerce/POS challenger; no unmeasured attribution causal claim; no provider selected |

## FM — FastMoss

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | FM / FastMoss |
| SOURCE_OWNER | FastMoss; exact legal entity UNKNOWN |
| SOURCE_URL / CLAIM | [E45](https://developers.fastmoss.com/mcp/overview); [E46](https://developer.fastmoss.com/home.html); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | TikTok Shop ecosystem; exact country roster UNKNOWN |
| SOURCE_TYPE | L3 estimated commerce/social analytics |
| SIGNAL_FAMILIES | DEMAND_INTELLIGENCE; PRODUCT_INTELLIGENCE; CHANNEL_MEASUREMENT; ADVERTISING_INTELLIGENCE; ATTENTION_INTELLIGENCE; CREATOR_INTELLIGENCE; COMPETITIVE_INTELLIGENCE; EMERGING_COMMERCE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Entitlement/account; exact price UNKNOWN |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / YES; see individual claim types / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L3 estimated commerce/social analytics; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | Shop/product/creator conceptual role; field coverage UNKNOWN |
| UPDATE_FREQUENCY | UNKNOWN |
| HISTORICAL_DEPTH | UNKNOWN |
| API | YES developer-center API advertised; endpoint/rates UNKNOWN |
| DATA_FEED | UNKNOWN |
| EXPORT | UNKNOWN |
| MCP_IF_ANY | YES advertised MCP |
| AUTOMATION_FEASIBILITY | CONDITIONAL on documented entitlement, scope, quota and rights; no implementation |
| AUTH_REQUIRED / PAID_REQUIRED | Entitlement/account; exact price UNKNOWN; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Reported GMV cannot be accepted as verified orders; completeness and rights unverified |
| FLOOOW_RELEVANCE | Material specialist beyond curated TikTok ads; China Douyin coverage not inferred |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | SPECIALIST_BENCHMARK; Material specialist beyond curated TikTok ads; China Douyin coverage not inferred; no provider selected |

## COMEX — Comex Stat / MDIC

| Field | Value |
|---|---|
| SOURCE_ID / SOURCE_NAME | COMEX / Comex Stat / MDIC |
| SOURCE_OWNER | Brazil MDIC / SECEX |
| SOURCE_URL / CLAIM | [E47](https://comexstat.mdic.gov.br/pt/home); [E48](https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/manuais-e-notas-metodologicas); exact substantive assertions and access observations in register |
| COUNTRY_OR_REGION | Brazil trade flows by partner/classification; not global retail |
| SOURCE_TYPE | L0 official trade statistics with revision/classification constraints |
| SIGNAL_FAMILIES | TRADE_INTELLIGENCE; SUPPLY_INTELLIGENCE; PRODUCT_INTELLIGENCE; EMERGING_COMMERCE_INTELLIGENCE |
| ACCESS_MODE | Documentation review only; Public data interface; no paid purchase |
| OBSERVED / SELF_REPORTED / INDEPENDENTLY_REPRODUCED | Public documentation/index review YES; underlying dataset NO / Platform documentation; performance/coverage not independently tested / NO |
| FIRST_PARTY / THIRD_PARTY_ESTIMATE | L0 official trade statistics with revision/classification constraints; vendor documentation is first-party about its product, not proof of original transaction lineage |
| DATA_GRANULARITY | NCM/partner/time aggregate; not retail SKU |
| UPDATE_FREQUENCY | Publication cadence/lag require release calendar; UNKNOWN in catalog |
| HISTORICAL_DEPTH | Portal offers historical data; exact audited depth UNKNOWN |
| API | UNKNOWN current supported API |
| DATA_FEED | Open CSV database documented |
| EXPORT | YES open CSV; exact license terms require check |
| MCP_IF_ANY | UNKNOWN |
| AUTOMATION_FEASIBILITY | UNKNOWN for required research fields; permitted manual sampling is a future alternative |
| AUTH_REQUIRED / PAID_REQUIRED | Public data interface; no paid purchase; exact dataset/feature paid requirement UNKNOWN unless explicit public resource |
| LEGAL_NOTES | Terms/privacy/local applicability review required before any collection; no evasion, credential purchase or access-control bypass |
| CONTRADICTIONS | Imports ≠ Brazilian sell-through; NCM many-to-many product mapping |
| FLOOOW_RELEVANCE | Official corroborating trade signal avoids all-commercial paid dependence |
| ADOPT_ADAPT_BENCHMARK_REJECT / RATIONALE | BENCHMARK; Official corroborating trade signal avoids all-commercial paid dependence; no provider selected |

## China access reality — function-specific, not inferred from an open-platform name

`PUBLIC_WEB_ACCESS` below means documentation access, not a representative consumer-market feed. `OPEN_API_AVAILABLE` means a documented developer interface, never anonymous unrestricted data. No login/account creation or regional access experiment was run. All Chinese portals have Chinese-language documentation; English terms are available for Temu. Language of every data field remains UNKNOWN.

| Source | PUBLIC_WEB_ACCESS | LOGIN_REQUIRED | CHINA_PHONE_REQUIRED | BUSINESS_ACCOUNT_REQUIRED | API_AVAILABLE / OPEN_API_AVAILABLE / PARTNER_API | SCRAPING_RESTRICTIONS | REGIONAL_ACCESS_CONSTRAINTS | LANGUAGE | CAPTCHA_OR_ANTI_BOT | HISTORICAL_ACCESS | EXPORTABILITY |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1688 | Corporate page read; developer fetch failed | UNKNOWN per function | UNKNOWN | UNKNOWN | UNKNOWN current verified scope; portal fetch failed / UNKNOWN verified research scope / UNKNOWN specific research partnership | UNKNOWN exact source terms; no scraping authorized by this review | UNKNOWN; tool errors do not establish regional prohibition | Chinese; other language support UNKNOWN | UNKNOWN; no bypass attempted | UNKNOWN representative history | UNKNOWN |
| TAO | Corporate/index only; developer fetch failed | UNKNOWN per function | UNKNOWN | UNKNOWN | UNKNOWN verified open.taobao.com scope; failed public fetch / UNKNOWN verified research scope / UNKNOWN specific research partnership | UNKNOWN exact source terms; no scraping authorized by this review | UNKNOWN; tool errors do not establish regional prohibition | Chinese; other language support UNKNOWN | UNKNOWN; no bypass attempted | UNKNOWN representative history | UNKNOWN |
| TMALL | Corporate/index only; shared developer scope UNKNOWN | UNKNOWN per function | UNKNOWN | UNKNOWN | UNKNOWN verified shared ecosystem API scope / UNKNOWN verified research scope / UNKNOWN specific research partnership | UNKNOWN exact source terms; no scraping authorized by this review | UNKNOWN; tool errors do not establish regional prohibition | Chinese; other language support UNKNOWN | UNKNOWN; no bypass attempted | UNKNOWN representative history | UNKNOWN |
| JD | Developer JS shell; legacy notice read | UNKNOWN per function | UNKNOWN | UNKNOWN | YES developer platform listed; research scope/rights UNKNOWN / Documented developer entry; anonymous market access UNKNOWN / UNKNOWN specific research partnership | UNKNOWN exact source terms; no scraping authorized by this review | UNKNOWN; tool errors do not establish regional prohibition | Chinese; other language support UNKNOWN | UNKNOWN; no bypass attempted | UNKNOWN representative history | UNKNOWN |
| DOU | Developer overview read | YES for documented authorized APIs; other features UNKNOWN | UNKNOWN | UNKNOWN | YES authorized platform capabilities; unrestricted commerce API NO evidence / Documented developer entry; anonymous market access UNKNOWN / UNKNOWN specific research partnership | UNKNOWN exact source terms; no scraping authorized by this review | UNKNOWN; tool errors do not establish regional prohibition | Chinese; other language support UNKNOWN | UNKNOWN; no bypass attempted | UNKNOWN representative history | UNKNOWN |
| XHS | Indexed commerce portal; direct timeout; account guide indexed | YES for documented authorized APIs; other features UNKNOWN | UNKNOWN | UNKNOWN | Account authorization documented; commerce portal indexed; research API UNKNOWN / UNKNOWN verified research scope / UNKNOWN specific research partnership | UNKNOWN exact source terms; no scraping authorized by this review | UNKNOWN; tool errors do not establish regional prohibition | Chinese; other language support UNKNOWN | UNKNOWN; no bypass attempted | UNKNOWN representative history | UNKNOWN |
| PDD | Official developer portal indexed | UNKNOWN per function | UNKNOWN | UNKNOWN | YES portal/API docs listed; current anonymous research API UNKNOWN / Documented developer entry; anonymous market access UNKNOWN / UNKNOWN specific research partnership | UNKNOWN exact source terms; no scraping authorized by this review | UNKNOWN; tool errors do not establish regional prohibition | Chinese; other language support UNKNOWN | UNKNOWN; no bypass attempted | UNKNOWN representative history | UNKNOWN |
| TEMU | Partner JS shell; official authorization/terms indexed | YES for documented authorized APIs; other features UNKNOWN | UNKNOWN | Permitted partner/seller roles; exact onboarding UNKNOWN | YES partner APIs; seller authorization for non-public shop management / Documented developer entry; anonymous market access UNKNOWN / UNKNOWN specific research partnership | UNKNOWN exact source terms; no scraping authorized by this review | Regional partner boundaries documented; exact eligibility UNKNOWN | Chinese; English terms documented | UNKNOWN; no bypass attempted | UNKNOWN representative history | Operational response not blanket research/export right |

## Source authority and missingness

L0: owned governed transactions, official government records and reconciled institutional records, within their precise scope. L1: first-party platform observations with aggregation/estimation retained. L2: observed listing/search/review/price records. L3: external estimates, projections and commercial intelligence. L4: community/creator weak signals. L5: Flooow hypotheses and forecasts. Level != truth. A purchase receipt, panel projection and supplier listing must never share an unlabeled sales field.

Missing metadata is UNKNOWN, not NO. None of the dispositions grants procurement, acquisition, integration, identity promotion or numeric confidence authority. Free public documentation, Google Trends/official ad interfaces and Comex CSV are proposed lower-cost research alternatives; completeness, reuse rights and labor cost remain to be measured.
