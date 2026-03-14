"""
W — Chay Carter's Personal Assistant
Google Sheets integration for the master connections spreadsheet.

Sheet columns expected (flexible — W adapts to what's there):
  Name | LinkedIn URL | Company | Role | Seniority | Status | Notes | Last Contact | Score
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ConnectionRecord:
    name: str
    linkedin_url: str
    company: str = ""
    role: str = ""
    seniority: str = ""           # founder/C-level/VP/Director/Senior/Other
    status: str = "target"        # target | connected | contacted | removed | pending
    notes: str = ""
    last_contact: str = ""
    relevance_score: int = 0      # 0–10 how neurotech-relevant they are
    source: str = ""              # how we found them


class SheetsManager:
    """
    Read/write the master connections spreadsheet.
    Supports Google Sheets (via gspread) or a local CSV fallback.
    """

    def __init__(self, sheet_id: str = "", credentials_path: str = "", log_callback=None):
        self.sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID", "")
        self.credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH", "")
        self.log = log_callback or (lambda msg, level="info": print(f"[{level}] {msg}"))
        self._gc = None
        self._sheet = None

    def _connect(self):
        """Connect to Google Sheets. Falls back to CSV if creds not available."""
        if not self.sheet_id or not self.credentials_path:
            self.log("No Google Sheets credentials — using local CSV mode.", "warning")
            return False
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            scopes = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
            self._gc = gspread.authorize(creds)
            self._sheet = self._gc.open_by_key(self.sheet_id).sheet1
            self.log("Connected to Google Sheet.", "success")
            return True
        except ImportError:
            self.log("gspread not installed. Run: pip install gspread google-auth", "warning")
            return False
        except Exception as e:
            self.log(f"Sheets connection error: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get_targets(self, status: str = "target") -> list[ConnectionRecord]:
        """Return all rows with the given status."""
        records = self._read_all()
        return [r for r in records if r.status == status]

    def get_all(self) -> list[ConnectionRecord]:
        return self._read_all()

    def _read_all(self) -> list[ConnectionRecord]:
        if self._connect() and self._sheet:
            return self._read_from_sheets()
        return self._read_from_csv()

    def _read_from_sheets(self) -> list[ConnectionRecord]:
        try:
            rows = self._sheet.get_all_records()
            return [self._row_to_record(r) for r in rows]
        except Exception as e:
            self.log(f"Error reading sheet: {e}", "error")
            return []

    def _read_from_csv(self, path: str = "data/master_connections.csv") -> list[ConnectionRecord]:
        import csv
        if not os.path.exists(path):
            return []
        records = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(self._row_to_record(row))
        return records

    def _row_to_record(self, row: dict) -> ConnectionRecord:
        # Flexible column name matching (handles various capitalisation)
        def get(keys):
            for k in keys:
                for rk, rv in row.items():
                    if rk.lower().strip() == k.lower():
                        return str(rv).strip()
            return ""

        return ConnectionRecord(
            name=get(["name", "full name"]),
            linkedin_url=get(["linkedin url", "linkedin", "url", "profile url"]),
            company=get(["company", "organisation", "organization"]),
            role=get(["role", "title", "job title", "position"]),
            seniority=get(["seniority", "level"]),
            status=get(["status"]) or "target",
            notes=get(["notes", "note"]),
            last_contact=get(["last contact", "last contacted", "date"]),
            relevance_score=int(get(["score", "relevance", "relevance score"]) or 0),
            source=get(["source"]),
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def update_status(self, linkedin_url: str, new_status: str, notes: str = ""):
        """Update a connection's status by LinkedIn URL."""
        if self._connect() and self._sheet:
            self._update_in_sheets(linkedin_url, new_status, notes)
        else:
            self._update_in_csv(linkedin_url, new_status, notes)

    def add_record(self, record: ConnectionRecord):
        """Add a new row to the spreadsheet."""
        if self._connect() and self._sheet:
            self._append_to_sheets(record)
        else:
            self._append_to_csv(record)

    def _update_in_sheets(self, linkedin_url: str, new_status: str, notes: str):
        try:
            cell = self._sheet.find(linkedin_url)
            if cell:
                headers = self._sheet.row_values(1)
                row = cell.row
                for i, h in enumerate(headers, 1):
                    if h.lower() in ("status",):
                        self._sheet.update_cell(row, i, new_status)
                    if notes and h.lower() in ("notes", "note"):
                        self._sheet.update_cell(row, i, notes)
                self.log(f"Updated {linkedin_url} → {new_status}", "success")
        except Exception as e:
            self.log(f"Sheet update error: {e}", "error")

    def _update_in_csv(self, linkedin_url: str, new_status: str, notes: str):
        import csv
        path = "data/master_connections.csv"
        if not os.path.exists(path):
            return
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            for row in reader:
                for k, v in row.items():
                    if v.strip() == linkedin_url:
                        row["status"] = new_status
                        if notes:
                            row["notes"] = notes
                rows.append(row)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def _append_to_sheets(self, record: ConnectionRecord):
        try:
            self._sheet.append_row([
                record.name, record.linkedin_url, record.company, record.role,
                record.seniority, record.status, record.notes,
                record.last_contact, record.relevance_score, record.source,
            ])
        except Exception as e:
            self.log(f"Sheet append error: {e}", "error")

    def _append_to_csv(self, record: ConnectionRecord):
        import csv
        path = "data/master_connections.csv"
        os.makedirs("data", exist_ok=True)
        file_exists = os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(record).keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(asdict(record))

    def export_summary(self) -> dict:
        """Return counts by status for the UI."""
        all_records = self.get_all()
        summary = {}
        for r in all_records:
            summary[r.status] = summary.get(r.status, 0) + 1
        summary["total"] = len(all_records)
        return summary
