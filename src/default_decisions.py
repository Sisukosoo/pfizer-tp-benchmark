"""Default manual triage decisions for the 55 Orbis comparables candidates."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from src import config

DEFAULT_MODIFIED_AT = datetime(2026, 5, 27, tzinfo=UTC).isoformat()


def make_decision_key(company_name: str, country: str) -> str:
    """Build a stable fallback key when an Orbis export lacks literal BvD IDs.

    Args:
        company_name: Company name from the Orbis export.
        country: Country from the Orbis export.

    Returns:
        Deterministic fallback identifier stored in the `bvd_id` field.
    """

    country_token = _slug(country)
    company_token = _slug(company_name)
    return f"FALLBACK:{country_token}:{company_token}"


def _accept(company_name: str, country: str) -> dict[str, Any]:
    """Create an accepted default decision record."""

    return _decision(company_name, country, config.DECISION_ACCEPT, None, None)


def _reject(
    company_name: str,
    country: str,
    reason: str,
    notes: str,
) -> dict[str, Any]:
    """Create a rejected default decision record."""

    return _decision(company_name, country, config.DECISION_REJECT, reason, notes)


def _decision(
    company_name: str,
    country: str,
    decision: str,
    reason: str | None,
    notes: str | None,
) -> dict[str, Any]:
    """Create a default decision record in the canonical schema."""

    return {
        "bvd_id": make_decision_key(company_name, country),
        "company_name": company_name,
        "country": country,
        "decision": decision,
        "reason": reason,
        "notes": notes,
        "modified_at": DEFAULT_MODIFIED_AT,
        "modified_by": "default",
    }


def _slug(value: str) -> str:
    """Normalize text for a stable fallback decision key."""

    normalized = re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")
    return re.sub(r"-+", "-", normalized)


DEFAULT_DECISIONS: tuple[dict[str, Any], ...] = (
    _reject(
        "ORIOLA OYJ",
        "Finland",
        config.CATEGORY_LOW_DATA_QUALITY,
        "Not covered by the manual accept list; baseline rejects pending validation.",
    ),
    _reject(
        "HERMANDAD FARMACEUTICA DEL MEDITERRANEO S.C.L.",
        "Spain",
        config.CATEGORY_COOPERATIVE,
        "Sociedad Cooperativa Limitada pharmacy cooperative.",
    ),
    _reject(
        "COOPERATIVA ESERCENTI FARMACIA SOC. COOP. A R.L. CON SIGLA CEF",
        "Italy",
        config.CATEGORY_COOPERATIVE,
        "Pharmacy cooperative structure.",
    ),
    _reject(
        "OPELLA HEALTHCARE INTERNATIONAL SAS",
        "France",
        config.CATEGORY_BRAND_OWNER,
        "Sanofi consumer health spin-off and brand owner.",
    ),
    _reject(
        "COOPERATIVE D'EXPLOITATION ET DE REPARTITION PHARMACEUTIQUE "
        "DE BRETAGNE ATLANTIQUE",
        "France",
        config.CATEGORY_COOPERATIVE,
        "Pharmacy cooperative and repartition entity.",
    ),
    _reject(
        "DOCMORRIS AG",
        "Switzerland",
        config.CATEGORY_RETAIL,
        "Online pharmacy and B2C retailer profile.",
    ),
    _reject(
        "UNNEFAR S.COOP.",
        "Spain",
        config.CATEGORY_COOPERATIVE,
        "Pharmacy cooperative.",
    ),
    _reject(
        "INTERCOS S.P.A.",
        "Italy",
        config.CATEGORY_MANUFACTURER,
        "Cosmetics manufacturer.",
    ),
    _reject(
        "GIPHAR GROUPE",
        "France",
        config.CATEGORY_COOPERATIVE,
        "Pharmacy chain group.",
    ),
    _reject(
        "CENTRAVET",
        "France",
        config.CATEGORY_WRONG_SEGMENT,
        "Veterinary pharmaceuticals.",
    ),
    _reject(
        "RICHARD KEHR GMBH & CO. KG",
        "Germany",
        config.CATEGORY_LOW_DATA_QUALITY,
        "Not covered by the manual accept list; baseline rejects pending validation.",
    ),
    _reject(
        "APOTEA AB",
        "Sweden",
        config.CATEGORY_RETAIL,
        "Online pharmacy retailer.",
    ),
    _reject(
        "GUACCI S.P.A.",
        "Italy",
        config.CATEGORY_LOW_DATA_QUALITY,
        "Not covered by the manual accept list; baseline rejects pending validation.",
    ),
    _reject(
        "UNIFARM S.P.A. UNIONE FARMACISTI TRENTINO-ALTO ADIGE",
        "Italy",
        config.CATEGORY_COOPERATIVE,
        "Unione Farmacisti pharmacy union.",
    ),
    _reject(
        "MULTIPHARMA GROUP",
        "Belgium",
        config.CATEGORY_LOW_DATA_QUALITY,
        "Not covered by the manual accept list; baseline rejects pending validation.",
    ),
    _reject(
        "FEDERFARMA.CO DISTRIBUZIONE E SERVIZI IN FARMACIA S.P.A.",
        "Italy",
        config.CATEGORY_COOPERATIVE,
        "Federazione Farmacisti network.",
    ),
    _reject(
        "VYGON",
        "France",
        config.CATEGORY_MANUFACTURER,
        "Medical and surgical equipment manufacturer.",
    ),
    _reject(
        "SMS MEDIPOOL AG",
        "Germany",
        config.CATEGORY_MANUFACTURER,
        "Pharmaceutical manufacturer.",
    ),
    _accept("TEDIS", "France"),
    _accept("PHARMAAND GMBH", "Austria"),
    _reject(
        "DISTRIBUIDORA FARMACEUTICA DE GIPUZKOA-GIPUZKOAKO FARMAZI BANATZAILEA SA",
        "Spain",
        config.CATEGORY_MIXED_PORTFOLIO,
        "Wholesale profile mixed with NACE 2110 pharmaceutical manufacturing signal.",
    ),
    _reject(
        "C.I.A.M. - SOCIETA' A RESPONSABILITA' LIMITATA",
        "Italy",
        config.CATEGORY_RETAIL,
        "Pet food retail activity.",
    ),
    _reject(
        "ASTUTE HEALTHCARE LIMITED",
        "United Kingdom",
        config.CATEGORY_MIXED_PORTFOLIO,
        "Wholesale and retail mix.",
    ),
    _reject(
        "ABF-PHARMAZIE GMBH & CO. KG",
        "Germany",
        config.CATEGORY_MANUFACTURER,
        "Compounding manufacturer.",
    ),
    _accept("UFM - UNIONE FARMACEUTICA MITO S.R.L.", "Italy"),
    _reject(
        "LBI COOPERATIVE SOCIETE ANONYME COOPERATIVE A CAPITAL VARIABLE",
        "France",
        config.CATEGORY_COOPERATIVE,
        "Pharmacy cooperative.",
    ),
    _reject(
        "MEDOVIA AB",
        "Sweden",
        config.CATEGORY_MIXED_PORTFOLIO,
        "Business description too generic and service-oriented.",
    ),
    _reject(
        "BRUNO FARMACEUTICI S.P.A.",
        "Italy",
        config.CATEGORY_BRAND_OWNER,
        "Italian pharma developer with own brands.",
    ),
    _reject(
        "CO.D.IN. MARCHE - CONSORZIO PER IL COORDINAMENTO DELLA DISTRIBU "
        "ZIONE INDIRETTA DEL FARMACO IN REGIME DI CONVENZIONE SPECIALE",
        "Italy",
        config.CATEGORY_COOPERATIVE,
        "Pharmacy distribution consortium.",
    ),
    _reject(
        "LAB LOGISTICS GROUP GMBH",
        "Germany",
        config.CATEGORY_LOGISTICS,
        "Logistics services for laboratory dealers.",
    ),
    _reject(
        "AMAPHARM GMBH",
        "Germany",
        config.CATEGORY_MANUFACTURER,
        "Gummy vitamin manufacturer.",
    ),
    _reject(
        "MEDAC SAS",
        "France",
        config.CATEGORY_MIXED_PORTFOLIO,
        "Niche pharmaceutical specialties with own marketing brands.",
    ),
    _accept("CLUB SALUTE S.P.A.", "Italy"),
    _reject(
        "IMMEDICA PHARMA AB",
        "Sweden",
        config.CATEGORY_BRAND_OWNER,
        "Develops, registers, and distributes pharmaceutical products.",
    ),
    _accept("PHARMORE GMBH", "Germany"),
    _reject(
        "MANA PHARMA SL.",
        "Spain",
        config.CATEGORY_MIXED_PORTFOLIO,
        "Medicines, devices, and cosmetics portfolio mix.",
    ),
    _reject(
        "CENTAURO VETERINARIA S.A.",
        "Spain",
        config.CATEGORY_WRONG_SEGMENT,
        "Primary activity linked to livestock and veterinary segment.",
    ),
    _accept("SAIMA S.P.A.", "Italy"),
    _reject(
        "MUNDIPHARMA VERWALTUNGSGESELLSCHAFT MIT BESCHRAENKTER HAFTUNG",
        "Germany",
        config.CATEGORY_HOLDING,
        "Holding company.",
    ),
    _accept("AMEFA GMBH", "Germany"),
    _reject(
        "SENTINEL CH. S.P.A.",
        "Italy",
        config.CATEGORY_WRONG_SEGMENT,
        "Diagnostic kits manufacturer.",
    ),
    _reject(
        "ECOFAR PRODUCTOS SL",
        "Spain",
        config.CATEGORY_MIXED_PORTFOLIO,
        "Pharmaceutical, parapharma, and medical-device portfolio mix.",
    ),
    _reject(
        "PEARL CHEMIST GROUP LIMITED",
        "United Kingdom",
        config.CATEGORY_RETAIL,
        "Retail pharmacy group.",
    ),
    _reject(
        "A1 PHARMACEUTICALS PUBLIC LIMITED COMPANY",
        "United Kingdom",
        config.CATEGORY_MANUFACTURER,
        "Manufacturing and wholesale activity mix.",
    ),
    _reject(
        "FARMACISTI ASSOCIATI PIEMONTE S.R.L. SIGLABILE IN F.A.P. S.R.L.",
        "Italy",
        config.CATEGORY_COOPERATIVE,
        "Pharmacists association.",
    ),
    _reject(
        "URSATEC GMBH",
        "Germany",
        config.CATEGORY_MANUFACTURER,
        "Packaging manufacturer.",
    ),
    _reject(
        "ZOLL MEDICAL FRANCE",
        "France",
        config.CATEGORY_WRONG_SEGMENT,
        "Medicosurgical materials, not pharma distribution.",
    ),
    _reject(
        "SANITAETSHAUS MUELLER-BETTEN GMBH & CO. KG",
        "Germany",
        config.CATEGORY_WRONG_SEGMENT,
        "Rehabilitation products and retail profile.",
    ),
    _accept("ALCYON ITALIA S.P.A.", "Italy"),
    _reject(
        "CHEMILINES GROUP HOLDINGS LIMITED",
        "United Kingdom",
        config.CATEGORY_MIXED_PORTFOLIO,
        "Pharmaceuticals mixed with perfumes and toiletries.",
    ),
    _reject(
        "AMPRI HANDELSGESELLSCHAFT MBH",
        "Germany",
        config.CATEGORY_WRONG_SEGMENT,
        "Medical and dental supplies.",
    ),
    _reject(
        "FARMACIE PARTENOPEE S.R.L.",
        "Italy",
        config.CATEGORY_COOPERATIVE,
        "Pharmacies association.",
    ),
    _reject(
        "VETCARE OY",
        "Finland",
        config.CATEGORY_WRONG_SEGMENT,
        "Veterinary and manufacturer profile.",
    ),
    _accept("BB FARMA SRL", "Italy"),
    _accept("MICERIUM S.P.A.", "Italy"),
)
