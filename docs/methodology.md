# Methodology: Rejection Cascade

This project benchmarks Pfizer Pharma GmbH as a tested party under the Transactional Net Margin Method (TNMM). The tested party is characterized as a Limited-Risk Distributor with Sales and Marketing functions (LRD-SM). The comparables workflow therefore seeks independent companies whose observed activity is broadly consistent with routine pharmaceutical distribution, while excluding entities with materially different functions, assets, risks, or product-market exposure.

The starting population is a fixed Orbis export of 55 EU/EFTA candidates selected with NACE 4646, Wholesale of pharmaceutical goods, and independence filters. The rejection cascade records the manual functional review as a reproducible decision ledger. Defaults are stored in `src/default_decisions.py`; runtime overrides are stored separately in `data/processed/comparables_decisions.csv`, which is intentionally gitignored because it is generated state.

The cascade excludes candidates in the following categories:

- Manufacturer: manufacturing or production assets make the company unlike a routine distributor.
- Pharmacy cooperative: member-owned pharmacy networks and consortia have structurally different economics.
- Retail / B2C: pharmacy chains and online retailers perform consumer-facing retail functions.
- Wrong product segment: medical devices, dental, rehabilitation, veterinary, diagnostics, packaging, or other non-pharma focus.
- Holding company: no relevant operating activity.
- Logistics service provider: service-provider logistics profile rather than principal distributor profile.
- Brand owner / IP profile: entities that own, develop, register, or market proprietary pharmaceutical brands.
- Mixed portfolio: pharma activity materially mixed with cosmetics, perfumes, devices, parapharmaceuticals, or own-marketed specialties.
- Low data quality: insufficient financial or business-description evidence to validate comparability.

The baseline result is 10 accepted comparables, 45 rejected candidates, and 0 pending candidates. User edits in the Streamlit app support sensitivity scenarios without overwriting the immutable baseline logic. This follows the OECD Transfer Pricing Guidelines' emphasis on comparability analysis, including paragraph 3.24 on practical considerations where markets are narrow and perfect comparables are scarce.
