from __future__ import annotations

from pathlib import Path

from controlled_docs.compliance import build_compliance_dashboard
from controlled_docs.utils import parse_date


def test_compliance_dashboard_flags_risks(populated_session, app_config, tmp_path: Path) -> None:
    output_path = tmp_path / "compliance.csv"
    rows = build_compliance_dashboard(
        populated_session,
        app_config,
        as_of_date=parse_date("2026-01-15"),
        output_path=output_path,
    )

    assert output_path.exists()
    assert any(row.risk_flag == "REAPPROVAL_OVERDUE" for row in rows)
    assert any(row.risk_flag == "DRAFT_IN_CONTROLLED_SET" for row in rows)
