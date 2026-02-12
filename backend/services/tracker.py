import csv
import json
import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class BewerbungsTracker:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.bewerbungen: list[dict[str, Any]] = []

        # Migration: CSV zu JSON falls CSV existiert
        csv_path = json_path.replace(".json", ".csv")
        if os.path.exists(csv_path) and not os.path.exists(json_path):
            self._migrate_from_csv(csv_path)
            os.remove(csv_path)
            logger.info("CSV-Daten nach JSON migriert und CSV gelöscht")
        elif os.path.exists(json_path):
            self._load_json()
        else:
            self._save_json()

    def _migrate_from_csv(self, csv_path: str) -> None:
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            for row in csv.DictReader(csvfile):
                self.bewerbungen.append(
                    {
                        "datum": row["datum"],
                        "firma": row["firma"],
                        "position": row["position"],
                        "ansprechpartner": row["ansprechpartner"],
                        "email": row.get("email", ""),
                        "quelle": row.get("quelle", ""),
                        "status": row["status"],
                        "pdf_pfad": row.get("pdf_pfad", ""),
                        "notizen": row.get("notizen", ""),
                        "betreff": "",
                        "email_text": "",
                    }
                )
        self._save_json()

    def _load_json(self) -> None:
        with open(self.json_path, encoding="utf-8") as f:
            self.bewerbungen = json.load(f)

    def _save_json(self) -> None:
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.bewerbungen, f, ensure_ascii=False, indent=2)

    def log_bewerbung(
        self,
        firma: str,
        position: str,
        ansprechpartner: str,
        email: str | None = None,
        quelle: str | None = None,
        status: str = "erstellt",
        pdf_pfad: str | None = None,
        notizen: str | None = None,
        betreff: str | None = None,
        email_text: str | None = None,
        links: dict[str, Any] | None = None,
    ) -> None:
        bewerbung = {
            "datum": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "firma": firma,
            "position": position,
            "ansprechpartner": ansprechpartner,
            "email": email or "",
            "quelle": quelle or "",
            "status": status,
            "pdf_pfad": pdf_pfad or "",
            "notizen": notizen or "",
            "betreff": betreff or "",
            "email_text": email_text or "",
            "links": links or {},
        }
        self.bewerbungen.append(bewerbung)
        self._save_json()

    def update_status(self, firma: str, datum: str, neuer_status: str) -> None:
        for bewerbung in self.bewerbungen:
            if bewerbung["firma"] == firma and bewerbung["datum"].startswith(datum):
                bewerbung["status"] = neuer_status
        self._save_json()

    def get_statistik(self) -> dict[str, int]:
        stats = {"gesamt": 0, "erstellt": 0, "versendet": 0, "antwort_erhalten": 0}
        for bewerbung in self.bewerbungen:
            stats["gesamt"] += 1
            status = bewerbung.get("status", "").lower()
            if status in stats:
                stats[status] += 1
        return stats

    def list_bewerbungen(self, limit: int = 10) -> None:
        if not self.bewerbungen:
            logger.info("Noch keine Bewerbungen vorhanden")
            return

        logger.info("\n%s", "=" * 80)
        logger.info("Letzte %s Bewerbungen:", min(limit, len(self.bewerbungen)))
        logger.info("%s\n", "=" * 80)

        for bew in self.bewerbungen[-limit:]:
            logger.info("Datum: %s", bew["datum"])
            logger.info("Firma: %s - %s", bew["firma"], bew["position"])
            logger.info("Ansprechpartner: %s", bew["ansprechpartner"])
            logger.info("Email: %s", bew["email"] if bew["email"] else "Keine E-Mail")
            logger.info("Status: %s", bew["status"])
            if bew.get("betreff"):
                logger.info("Betreff: %s", bew["betreff"])
            if bew.get("notizen"):
                logger.info("Notizen: %s", bew["notizen"])
            logger.info("%s\n", "-" * 80)

    def get_latest_bewerbung(self) -> dict[str, Any] | None:
        return self.bewerbungen[-1] if self.bewerbungen else None
