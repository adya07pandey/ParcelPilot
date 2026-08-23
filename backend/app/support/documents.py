from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

from pypdf import PdfReader

from app.models import Account

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"

DOCUMENTS = {
    "01_Support_Policy_v3_CURRENT.pdf": {
        "document_id": "support-policy-v3",
        "name": "Support Policy v3",
        "type": "General Policy",
        "document_type": "support_policy",
        "status": "CURRENT",
        "effective": "1 May 2026",
        "scope": "GLOBAL",
        "authority": 4,
    },
    "02_Support_Policy_v2_DEPRECATED.pdf": {
        "document_id": "support-policy-v2",
        "name": "Support Policy v2",
        "type": "General Policy",
        "document_type": "support_policy",
        "status": "DEPRECATED",
        "effective": "1 Jan 2025 - 30 Apr 2026",
        "scope": "GLOBAL",
        "authority": 2,
    },
    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {
        "document_id": "cancellation-service-credit-sop-v4",
        "name": "Cancellation & Service Credit SOP v4",
        "type": "General Policy",
        "document_type": "sop",
        "status": "CURRENT",
        "effective": "15 June 2026",
        "scope": "GLOBAL",
        "authority": 4,
    },
    "04_Product_Operations_Guide_and_Known_Issues.pdf": {
        "document_id": "product-operations-guide",
        "name": "Product Operations Guide",
        "type": "General Policy",
        "document_type": "product_guide",
        "status": "CURRENT",
        "effective": "14 Aug 2026",
        "scope": "GLOBAL",
        "authority": 3,
    },
    "05_Northstar_Logistics_Enterprise_Agreement.pdf": {
        "document_id": "northstar-enterprise-agreement",
        "name": "Northstar Logistics Enterprise Agreement",
        "type": "Company Agreement",
        "document_type": "customer_agreement",
        "status": "ACTIVE",
        "effective": "1 Jan 2026 - 31 Dec 2026",
        "scope": "ACCOUNT",
        "account_id": "ACCT-001",
        "authority": 5,
    },
    "06_LumenWorks_Service_Agreement.pdf": {
        "document_id": "lumenworks-service-agreement",
        "name": "LumenWorks Service Agreement",
        "type": "Company Agreement",
        "document_type": "customer_agreement",
        "status": "ACTIVE",
        "effective": "1 Mar 2026 - 28 Feb 2027",
        "scope": "ACCOUNT",
        "account_id": "ACCT-002",
        "authority": 5,
    },
}


@lru_cache(maxsize=16)
def read_document_text(filename: str) -> str:
    path = DATA_DIR / filename
    if not path.exists():
        return ""
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return normalize_text(text)


def general_policy_records() -> list[dict]:
    return [
        build_document_record(filename)
        for filename, metadata in DOCUMENTS.items()
        if metadata["scope"] == "GLOBAL"
    ]


def agreement_record_for_account(account: Account) -> dict:
    filename = account.contract_file
    if filename and filename in DOCUMENTS:
        record = build_document_record(filename)
    else:
        record = fallback_agreement_record(account)
    record["account_id"] = account.account_id
    record["account_name"] = account.account_name
    record["plan"] = account.plan
    return record


def agreement_records_for_accounts(accounts: list[Account]) -> list[dict]:
    return [agreement_record_for_account(account) for account in accounts if account.contract_file]


def build_document_record(filename: str) -> dict:
    metadata = DOCUMENTS[filename]
    text = read_document_text(filename)
    return {
        **metadata,
        "source_file": filename,
        "document": filename,
        "summary": summarize_document(metadata["document_id"], text),
        "terms": extract_terms(metadata["document_id"], text),
        "excerpt": text[:700],
    }


def fallback_agreement_record(account: Account) -> dict:
    return {
        "document_id": account.contract_file or account.account_id,
        "name": f"{account.account_name} Agreement",
        "type": "Company Agreement",
        "document_type": "customer_agreement",
        "status": "UNKNOWN",
        "effective": "Not available",
        "scope": "ACCOUNT",
        "authority": 5,
        "source_file": account.contract_file,
        "document": account.contract_file,
        "summary": "No matching agreement PDF was found in the data folder.",
        "terms": {
            "support": "Agreement PDF not available.",
            "cancellation": "Agreement PDF not available.",
            "service_credits": "Agreement PDF not available.",
            "override": "Use general policy unless a signed agreement is available.",
        },
        "excerpt": "",
    }


def extract_terms(document_id: str, text: str) -> dict:
    if document_id == "northstar-enterprise-agreement":
        return {
            "support": "P1: 15 minutes, 24x7; P2: 1 hour; P3: 8 business hours.",
            "cancellation": "Northstar may cancel any BOOKED shipment before pickup with no cancellation fee, regardless of booking age. PICKED_UP uses return-to-origin.",
            "service_credits": "Monthly aggregate service credits are capped at INR 5,000; otherwise the current service-credit SOP applies.",
            "override": "This signed enterprise agreement overrides generic support and cancellation rules where it explicitly applies.",
        }
    if document_id == "lumenworks-service-agreement":
        return {
            "support": "P1: 2 business hours; P2: 4 business hours; P3: 2 business days. No weekend or after-hours support coverage.",
            "cancellation": "No special cancellation-fee waiver applies; use the current ParcelPilot Cancellation & Service Credit SOP.",
            "service_credits": "Failed-pickup credit applies after more than 4 hours past the pickup-window end when the carrier is at fault and the customer is not at fault; fixed credit is INR 300.",
            "override": "The failed-pickup credit threshold and amount replace the default SOP for LumenWorks.",
        }
    if document_id == "support-policy-v3":
        return {
            "support": "Default targets: Enterprise P1 30 min / P2 2 hours / P3 1 business day; Growth P1 2 business hours / P2 4 business hours / P3 2 business days; Standard P1 4 business hours / P2 1 business day / P3 2 business days.",
            "cancellation": "Not covered here.",
            "service_credits": "Not covered here.",
            "override": "A signed customer agreement takes precedence, then current support policy, then current product documentation.",
        }
    if document_id == "cancellation-service-credit-sop-v4":
        return {
            "support": "Not covered here.",
            "cancellation": "DRAFT cancels free. BOOKED before pickup cancels free within 30 minutes; after 30 minutes INR 250 applies unless a customer agreement waives it. PICKED_UP uses return-to-origin; DELIVERED cannot cancel.",
            "service_credits": "Default failed-pickup credit requires pickup more than 2 hours late, carrier fault, and no customer fault; credit is lower of INR 500 or 10% of shipment fee.",
            "override": "A signed customer agreement may replace delay threshold, credit amount, or cap.",
        }
    if document_id == "product-operations-guide":
        return {
            "support": "Product behavior and known issue guidance.",
            "cancellation": "Not covered here.",
            "service_credits": "Not covered here.",
            "override": "Use for product facts and known issues after agreement and policy evidence.",
        }
    return {
        "support": first_matching_sentence(text, ["P1", "support"], "See source document."),
        "cancellation": first_matching_sentence(text, ["cancel"], "See source document."),
        "service_credits": first_matching_sentence(text, ["credit"], "See source document."),
        "override": first_matching_sentence(text, ["override", "replace"], "Use source precedence rules."),
    }


def summarize_document(document_id: str, text: str) -> str:
    terms = extract_terms(document_id, text)
    if document_id.endswith("agreement"):
        return " ".join([terms["support"], terms["cancellation"], terms["service_credits"]])
    if document_id == "support-policy-v3":
        return "Current support severity definitions, first-response targets, escalation, and source precedence."
    if document_id == "support-policy-v2":
        return "Deprecated support policy retained only for historical questions."
    if document_id == "cancellation-service-credit-sop-v4":
        return "Current cancellation, return-to-origin, and failed-pickup service-credit rules."
    if document_id == "product-operations-guide":
        return "Current product capabilities and known issue guidance for bulk upload, shipment status, and carrier webhooks."
    return text[:220]


def first_matching_sentence(text: str, words: list[str], fallback: str) -> str:
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        lower = sentence.lower()
        if all(word.lower() in lower for word in words):
            return sentence
    return fallback


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()
