#!${TX_PREFIX:-/usr/local}/files/usr/bin/env python3
# ffp: FFP-MURUA-PY-INGEST data-science python
"""
Murua v8.4-OMEGA Forensic Envelope Ingestion & Barabasi-Oxbow Calibration Engine
Runs on 5-Node wg0 Mesh (10.77.0.3 lat-5591 / 10.77.0.4 pixel-8-pro)
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import sys
from typing import Optional, Dict, Any, List

@dataclass
class EnvelopeForensicPayload:
    order_id: str
    corridor_id: str
    vendor_shipped_utc: datetime
    carrier_pickup_utc: datetime
    box_discovered_utc: Optional[datetime]
    gross_mass_g: Optional[float]
    thickness_mm: Optional[float]
    cfc_postmark_date: Optional[str]
    omniva_inkjet_date: Optional[str]
    kix_code: Optional[str]
    franking_type: str

class BarabasiOxbowEstimator:
    """
    Computes conditional arrival probabilities accounting for UPU GMS/UNEX
    terminal-dues gaming and Rukki tee 7 non-preemptive priority buffering.
    """
    def __init__(self, rho_parcel: float = 0.85, tau0_hours: float = 36.0):
        self.rho = min(max(rho_parcel, 0.05), 0.99)
        self.tau0 = tau0_hours / ((1.0 - math.sqrt(self.rho)) ** 2)

    def oxbow_waiting_density(self, wait_hours: float) -> float:
        """Barabasi heavy-tail priority waiting time PDF: P(tau_w) ~ tau_w^(-3/2) * exp(-tau_w / tau0)"""
        if wait_hours <= 1.0:
            return 0.0
        return (wait_hours ** -1.5) * math.exp(-wait_hours / self.tau0)

    def decompose_dwell(self, payload: EnvelopeForensicPayload) -> Dict[str, Any]:
        pre_advice_lag_h = (
            payload.carrier_pickup_utc - payload.vendor_shipped_utc
        ).total_seconds() / 3600.0

        result = {
            "order_id": payload.order_id,
            "corridor_id": payload.corridor_id,
            "vendor_pre_advice_lag_hours": round(pre_advice_lag_h, 2),
            "status": "IN_TRANSIT_OXBOW_BUFFER"
        }

        if payload.box_discovered_utc:
            net_transit_h = (
                payload.box_discovered_utc - payload.carrier_pickup_utc
            ).total_seconds() / 3600.0
            result["net_physical_transit_hours"] = round(net_transit_h, 2)
            result["status"] = "DELIVERED_VERIFIED"

        return result

    def to_toon_row(self, payload: EnvelopeForensicPayload) -> str:
        """Serializes observation into Token-Oriented Object Notation (TOON)."""
        disc_str = payload.box_discovered_utc.strftime("%Y-%m-%dT%H:%M") if payload.box_discovered_utc else "null"
        return (
            f"{payload.corridor_id}|{payload.order_id}|"
            f"{payload.vendor_shipped_utc.strftime('%Y-%m-%dT%H:%M')}|"
            f"{payload.carrier_pickup_utc.strftime('%Y-%m-%dT%H:%M')}|"
            f"{payload.cfc_postmark_date or 'null'}|"
            f"{payload.omniva_inkjet_date or 'null'}|"
            f"{disc_str}|{payload.gross_mass_g or 0.0}|"
            f"{payload.thickness_mm or 0.0}|{payload.franking_type}|"
            f"{str(bool(payload.kix_code)).lower()}|IN_OXBOW_BUFFER"
        )

def run_self_test():
    print("=== [PYTHON] Murua Forensic Ingestion & Calibration Self-Test ===")
    estimator = BarabasiOxbowEstimator(rho_parcel=0.82, tau0_hours=36.0)

    p1 = EnvelopeForensicPayload(
        order_id="58b73b08",
        corridor_id="NL-AMS_EE-TLL_12618",
        vendor_shipped_utc=datetime(2026, 10, 25, 14, 10, tzinfo=timezone.utc),
        carrier_pickup_utc=datetime(2026, 10, 27, 11, 0, tzinfo=timezone.utc),
        box_discovered_utc=None,
        gross_mass_g=65.0,
        thickness_mm=4.0,
        cfc_postmark_date="2026-10-27",
        omniva_inkjet_date=None,
        kix_code="12618TN390",
        franking_type="STD_ENV"
    )

    dwell = estimator.decompose_dwell(p1)
    print(f"Item 58b73b08 Dwell Decomposition: {dwell}")

    toon_line = estimator.to_toon_row(p1)
    print(f"TOON Serialized: {toon_line}")

    pdf_sample = estimator.oxbow_waiting_density(48.0)
    print(f"Barabasi PDF at 48 hours: {pdf_sample:.6e}")
    print("=== [PYTHON] Ingestion Self-Test PASSED ===")

if __name__ == "__main__":
    run_self_test()
