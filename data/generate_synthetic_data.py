from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from controlled_docs.utils import ensure_parent_dir, stable_uuid


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DOCS_DIR = DATA_DIR / "docs"
REGISTER_PATH = DATA_DIR / "document_register.xlsx"
BENCHMARK_PATH = DATA_DIR / "qa_benchmark.jsonl"


DOCUMENT_SPECS = [
    {
        "document_key": "USFDA_BATCH_RECORD_REVIEW",
        "title": "SOP Batch Record Review",
        "doc_type": "SOP",
        "jurisdiction": "US-FDA",
        "owner": "Quality Systems",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-03-01",
                "purpose": "Control the review of batch production records before lot release.",
                "clauses": [
                    {
                        "question": "As of 2024-06-30, within how many business days must batch records be reviewed after manufacturing completion?",
                        "answer": "Batch production records shall be reviewed within 2 business days after manufacturing completion.",
                    },
                    {
                        "question": "What must the reviewer do if a critical deviation is discovered during US-FDA batch record review?",
                        "answer": "The reviewer shall escalate any critical deviation to the site quality head within 1 business day.",
                    },
                    {
                        "question": "Who must sign the batch record disposition in the older US-FDA SOP?",
                        "answer": "A quality assurance reviewer and the manufacturing supervisor shall sign the batch record disposition.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-10-01",
                "purpose": "Tighten review timing following an inspection observation.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, within how many business days must batch records be reviewed after manufacturing completion?",
                        "answer": "Batch production records shall be reviewed within 1 business day after manufacturing completion.",
                    },
                    {
                        "question": "In the current US-FDA batch record SOP, when must a critical deviation be escalated?",
                        "answer": "The reviewer shall escalate any critical deviation to the site quality head immediately and no later than 4 hours from discovery.",
                    },
                    {
                        "question": "Who signs the batch record disposition in the current approved version?",
                        "answer": "A quality assurance reviewer, the manufacturing supervisor, and the release authorizer shall sign the batch record disposition.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "USFDA_COMPLAINT_TRIAGE",
        "title": "SOP Complaint Triage and MDR Assessment",
        "doc_type": "SOP",
        "jurisdiction": "US-FDA",
        "owner": "Post-Market Surveillance",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-01-15",
                "purpose": "Standardize initial complaint triage and MDR screening.",
                "clauses": [
                    {
                        "question": "Before 2025-09-01, how quickly did the complaint unit need to complete initial triage?",
                        "answer": "Initial complaint triage shall be completed within 5 calendar days of complaint receipt.",
                    },
                    {
                        "question": "What was the follow-up timing for missing complainant information in the older US-FDA complaint SOP?",
                        "answer": "Missing complainant information shall be requested within 3 business days of case opening.",
                    },
                    {
                        "question": "How long did personnel have to escalate potential MDR events in version 1 of the complaint SOP?",
                        "answer": "Potential MDR events shall be escalated to Regulatory Affairs within 2 business days.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-09-01",
                "purpose": "Accelerate adverse event assessment timelines.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, how quickly must the complaint unit complete initial triage?",
                        "answer": "Initial complaint triage shall be completed within 2 calendar days of complaint receipt.",
                    },
                    {
                        "question": "In the current US-FDA complaint SOP, when is missing complainant information requested?",
                        "answer": "Missing complainant information shall be requested on the same business day that the case is opened.",
                    },
                    {
                        "question": "How fast must potential MDR events be escalated in the current complaint SOP?",
                        "answer": "Potential MDR events shall be escalated to Regulatory Affairs within 1 business day.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "EUMDR_STERILIZATION_RELEASE",
        "title": "Work Instruction Sterilization Load Release",
        "doc_type": "WI",
        "jurisdiction": "EU-MDR",
        "owner": "Manufacturing Engineering",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-02-10",
                "purpose": "Define evidence needed before sterilized load release.",
                "clauses": [
                    {
                        "question": "Under the older EU-MDR sterilization instruction, how often was a biological indicator required?",
                        "answer": "A biological indicator challenge shall be run at least once per week for each validated sterilizer.",
                    },
                    {
                        "question": "What record had to be attached before releasing a sterilization load in version 1?",
                        "answer": "The sterilization batch packet shall include the signed load configuration record before release.",
                    },
                    {
                        "question": "Who could release a sterilization load under version 1 of the EU-MDR work instruction?",
                        "answer": "A manufacturing engineer or a designated quality engineer may release a sterilization load.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-07-01",
                "purpose": "Increase release evidence after an audit observation.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, how often is a biological indicator required for EU-MDR sterilization release?",
                        "answer": "A biological indicator challenge shall be run for every sterilization load before release.",
                    },
                    {
                        "question": "What record must be attached before releasing a sterilization load in the current version?",
                        "answer": "The sterilization batch packet shall include the signed load configuration record and the calibrated sensor printout before release.",
                    },
                    {
                        "question": "Who may release a sterilization load in the current EU-MDR instruction?",
                        "answer": "Only a designated quality engineer may release a sterilization load after sterilization evidence review.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "ISO_SUPPLIER_QUALIFICATION",
        "title": "Policy Supplier Qualification and Monitoring",
        "doc_type": "POLICY",
        "jurisdiction": "ISO13485",
        "owner": "Supplier Quality",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-01-05",
                "purpose": "Define baseline supplier qualification expectations.",
                "clauses": [
                    {
                        "question": "In the older ISO13485 supplier policy, how often were high-risk suppliers audited on site?",
                        "answer": "High-risk suppliers shall receive an on-site audit at least once every 12 months.",
                    },
                    {
                        "question": "What score triggered supplier escalation in version 1 of the supplier policy?",
                        "answer": "A quarterly supplier performance score below 80 shall trigger escalation to the Supplier Review Board.",
                    },
                    {
                        "question": "What approval was required before adding a critical supplier under version 1?",
                        "answer": "Quality and Procurement directors shall approve the addition of a critical supplier.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-06-15",
                "purpose": "Reduce surveillance interval for high-risk suppliers.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, how often are high-risk suppliers audited on site under ISO13485?",
                        "answer": "High-risk suppliers shall receive an on-site audit at least once every 9 months.",
                    },
                    {
                        "question": "What score triggers supplier escalation in the current supplier policy?",
                        "answer": "A quarterly supplier performance score below 85 shall trigger escalation to the Supplier Review Board.",
                    },
                    {
                        "question": "What approvals are required before adding a critical supplier in the current version?",
                        "answer": "Quality, Procurement, and Regulatory directors shall approve the addition of a critical supplier.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "USFDA_DATA_INTEGRITY_TRAINING",
        "title": "Training Record Data Integrity Refresher",
        "doc_type": "TRAINING",
        "jurisdiction": "US-FDA",
        "owner": "Training Administration",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-04-01",
                "purpose": "Maintain baseline data integrity refresher training frequency.",
                "clauses": [
                    {
                        "question": "Before 2025-08-01, how often did operators need data integrity refresher training?",
                        "answer": "Operators shall complete data integrity refresher training every 12 months.",
                    },
                    {
                        "question": "What minimum quiz score was required in the older data integrity training record?",
                        "answer": "A minimum quiz score of 80 percent is required to complete the refresher training.",
                    },
                    {
                        "question": "How quickly did supervisors need to assign makeup training under the older record?",
                        "answer": "Supervisors shall assign makeup training within 10 business days of a missed session.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-08-01",
                "purpose": "Increase refresher frequency for high-risk roles.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, how often must operators complete US-FDA data integrity refresher training?",
                        "answer": "Operators shall complete data integrity refresher training every 180 days.",
                    },
                    {
                        "question": "What minimum quiz score is required in the current data integrity training record?",
                        "answer": "A minimum quiz score of 90 percent is required to complete the refresher training.",
                    },
                    {
                        "question": "How quickly must supervisors assign makeup training in the current record?",
                        "answer": "Supervisors shall assign makeup training within 5 business days of a missed session.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "EUMDR_NONCONFORMING_CAPA",
        "title": "CAPA Summary Nonconforming Material Escalation",
        "doc_type": "CAPA",
        "jurisdiction": "EU-MDR",
        "owner": "Quality Engineering",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-05-20",
                "purpose": "Track recurring nonconforming material CAPA actions.",
                "clauses": [
                    {
                        "question": "In the earlier EU-MDR CAPA summary, when was effectiveness verification performed?",
                        "answer": "Effectiveness verification shall be completed within 30 calendar days of CAPA action closure.",
                    },
                    {
                        "question": "What threshold triggered supplier containment under version 1 of the CAPA summary?",
                        "answer": "Three repeat nonconformances from the same supplier in a quarter shall trigger supplier containment.",
                    },
                    {
                        "question": "Who chaired the CAPA review board under the older CAPA summary?",
                        "answer": "The Quality Engineering manager shall chair the monthly CAPA review board.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-11-15",
                "purpose": "Add faster escalation for recurring nonconforming material.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, when is effectiveness verification performed for the EU-MDR CAPA summary?",
                        "answer": "Effectiveness verification shall be completed within 21 calendar days of CAPA action closure.",
                    },
                    {
                        "question": "What threshold triggers supplier containment in the current CAPA summary?",
                        "answer": "Two repeat nonconformances from the same supplier in a quarter shall trigger supplier containment.",
                    },
                    {
                        "question": "Who chairs the CAPA review board in the current summary?",
                        "answer": "The Quality Engineering manager and the Operations director shall jointly chair the monthly CAPA review board.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "EUMDR_UDI_VERIFICATION",
        "title": "SOP UDI Label Verification",
        "doc_type": "SOP",
        "jurisdiction": "EU-MDR",
        "owner": "Labeling Operations",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-07-01",
                "purpose": "Control label verification prior to packaging release.",
                "clauses": [
                    {
                        "question": "Under the older EU-MDR UDI SOP, how many people reviewed the final label proof?",
                        "answer": "One labeling specialist shall review the final label proof before packaging release.",
                    },
                    {
                        "question": "What barcode grade was acceptable in version 1 of the UDI verification SOP?",
                        "answer": "A barcode verification grade of C or better is acceptable for release.",
                    },
                    {
                        "question": "When did translation discrepancies need to be escalated in the older UDI SOP?",
                        "answer": "Translation discrepancies shall be escalated before the affected lot is packaged.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-12-01",
                "purpose": "Add a second-person check for multilingual label content.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, how many people review the final label proof under the EU-MDR UDI SOP?",
                        "answer": "Two qualified reviewers shall review the final label proof before packaging release.",
                    },
                    {
                        "question": "What barcode grade is acceptable in the current UDI verification SOP?",
                        "answer": "A barcode verification grade of B or better is acceptable for release.",
                    },
                    {
                        "question": "When must translation discrepancies be escalated in the current UDI SOP?",
                        "answer": "Translation discrepancies shall be escalated within 4 hours of detection and before the affected lot is packaged.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "USFDA_ELECTRONIC_RECORDS_POLICY",
        "title": "Policy Electronic Records and Signatures",
        "doc_type": "POLICY",
        "jurisdiction": "US-FDA",
        "owner": "IT Quality",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-02-01",
                "purpose": "Establish baseline Part 11 controls for electronic records.",
                "clauses": [
                    {
                        "question": "In the older electronic records policy, how often were privileged account passwords rotated?",
                        "answer": "Privileged account passwords shall be rotated every 90 days.",
                    },
                    {
                        "question": "What dual-review requirement applied to electronic signature exception logs in version 1?",
                        "answer": "Electronic signature exception logs shall be reviewed monthly by IT Quality and System Administration.",
                    },
                    {
                        "question": "How quickly were inactive administrator accounts disabled under version 1 of the policy?",
                        "answer": "Inactive administrator accounts shall be disabled within 24 hours of role change.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-05-01",
                "purpose": "Move to risk-based access controls with tighter account disablement.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, how often are privileged account passwords rotated in the US-FDA electronic records policy?",
                        "answer": "Privileged account passwords shall be rotated every 60 days.",
                    },
                    {
                        "question": "What review requirement applies to electronic signature exception logs in the current policy?",
                        "answer": "Electronic signature exception logs shall be reviewed every two weeks by IT Quality and System Administration.",
                    },
                    {
                        "question": "How quickly are inactive administrator accounts disabled in the current policy?",
                        "answer": "Inactive administrator accounts shall be disabled within 8 hours of role change.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "ISO_DMR_UPDATE_WI",
        "title": "Work Instruction Device Master Record Update",
        "doc_type": "WI",
        "jurisdiction": "ISO13485",
        "owner": "Document Control",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-03-18",
                "purpose": "Control update sequencing for device master record packages.",
                "clauses": [
                    {
                        "question": "In the older ISO13485 DMR work instruction, who approved master record updates?",
                        "answer": "Quality Assurance shall approve device master record updates before release.",
                    },
                    {
                        "question": "How long did engineering have to attach redlines under version 1 of the DMR instruction?",
                        "answer": "Engineering shall attach redlined drawings within 3 business days of the change order approval.",
                    },
                    {
                        "question": "What training prerequisite existed for DMR editors under the older work instruction?",
                        "answer": "Only trained document control specialists may update released sections of the device master record.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-09-20",
                "purpose": "Add regulatory co-approval for higher risk record changes.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, who approves device master record updates under ISO13485?",
                        "answer": "Quality Assurance and Regulatory Affairs shall approve device master record updates before release.",
                    },
                    {
                        "question": "How long does engineering have to attach redlines in the current DMR instruction?",
                        "answer": "Engineering shall attach redlined drawings within 1 business day of the change order approval.",
                    },
                    {
                        "question": "What training prerequisite exists for DMR editors in the current work instruction?",
                        "answer": "Only trained document control specialists with annual refresher completion may update released sections of the device master record.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "EUMDR_PMS_TRAINING",
        "title": "Training Record Post-Market Surveillance Review",
        "doc_type": "TRAINING",
        "jurisdiction": "EU-MDR",
        "owner": "Clinical Affairs",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-06-01",
                "purpose": "Document PMS reviewer readiness on an annual cadence.",
                "clauses": [
                    {
                        "question": "Under the older EU-MDR PMS training record, how often was refresher training required?",
                        "answer": "Post-market surveillance reviewers shall complete refresher training every 12 months.",
                    },
                    {
                        "question": "What passing score applied to PMS training in version 1?",
                        "answer": "A passing score of 85 percent is required for the PMS refresher assessment.",
                    },
                    {
                        "question": "How quickly did overdue PMS training require escalation in the older record?",
                        "answer": "Overdue PMS training shall be escalated to Clinical Affairs leadership after 15 calendar days.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-10-10",
                "purpose": "Increase PMS refresher frequency after a notified body review.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, how often is EU-MDR PMS refresher training required?",
                        "answer": "Post-market surveillance reviewers shall complete refresher training every 6 months.",
                    },
                    {
                        "question": "What passing score applies to the current PMS training record?",
                        "answer": "A passing score of 90 percent is required for the PMS refresher assessment.",
                    },
                    {
                        "question": "How quickly does overdue PMS training require escalation in the current record?",
                        "answer": "Overdue PMS training shall be escalated to Clinical Affairs leadership after 7 calendar days.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "ISO_INTERNAL_AUDIT_CAPA",
        "title": "CAPA Summary Internal Audit Escalation",
        "doc_type": "CAPA",
        "jurisdiction": "ISO13485",
        "owner": "Internal Audit",
        "status": "APPROVED",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2024-04-25",
                "purpose": "Track CAPA commitments from internal audit findings.",
                "clauses": [
                    {
                        "question": "In the older ISO13485 internal audit CAPA summary, when was closure expected?",
                        "answer": "Internal audit CAPA items shall be closed within 60 calendar days unless an extension is approved.",
                    },
                    {
                        "question": "What threshold required executive visibility in version 1 of the internal audit CAPA summary?",
                        "answer": "More than five overdue internal audit CAPA items shall trigger executive review.",
                    },
                    {
                        "question": "Who approved CAPA deadline extensions under the older summary?",
                        "answer": "The Internal Audit manager shall approve CAPA deadline extensions.",
                    },
                ],
            },
            {
                "version_number": 2,
                "effective_date": "2025-11-01",
                "purpose": "Tighten closure timing for recurring system findings.",
                "clauses": [
                    {
                        "question": "As of 2026-01-15, when are internal audit CAPA items expected to close under ISO13485?",
                        "answer": "Internal audit CAPA items shall be closed within 45 calendar days unless an extension is approved.",
                    },
                    {
                        "question": "What threshold requires executive visibility in the current internal audit CAPA summary?",
                        "answer": "More than three overdue internal audit CAPA items shall trigger executive review.",
                    },
                    {
                        "question": "Who approves CAPA deadline extensions in the current internal audit summary?",
                        "answer": "The Internal Audit manager and the Head of Quality shall approve CAPA deadline extensions.",
                    },
                ],
            },
        ],
    },
    {
        "document_key": "USFDA_LAB_INVESTIGATION_DRAFT",
        "title": "SOP Laboratory Investigation Escalation",
        "doc_type": "SOP",
        "jurisdiction": "US-FDA",
        "owner": "QC Laboratory",
        "status": "DRAFT",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2026-02-01",
                "purpose": "Draft update not yet approved for controlled use.",
                "clauses": [
                    {
                        "question": "In the draft laboratory investigation SOP, how quickly are phase 1 investigations documented?",
                        "answer": "Phase 1 laboratory investigations shall be documented within 8 hours of result confirmation.",
                    },
                    {
                        "question": "Who approves the draft laboratory investigation report?",
                        "answer": "The QC manager and the site quality head shall approve the laboratory investigation report.",
                    },
                    {
                        "question": "What sample retention rule appears in the draft laboratory investigation SOP?",
                        "answer": "Retained samples from invalid assay investigations shall be preserved for 18 months.",
                    },
                ],
            }
        ],
    },
    {
        "document_key": "EUMDR_TRANSLATION_MEMO_OBSOLETE",
        "title": "Policy Memo Legacy Translation Control",
        "doc_type": "POLICY",
        "jurisdiction": "EU-MDR",
        "owner": "Regulatory Affairs",
        "status": "OBSOLETE",
        "versions": [
            {
                "version_number": 1,
                "effective_date": "2023-12-01",
                "purpose": "Legacy translation control memo retained for audit reference only.",
                "clauses": [
                    {
                        "question": "In the obsolete EU-MDR translation memo, who approved translation updates?",
                        "answer": "Regulatory Affairs alone approved translation updates before release.",
                    },
                    {
                        "question": "What archival timing appears in the obsolete translation memo?",
                        "answer": "Superseded translations shall be archived within 10 business days.",
                    },
                    {
                        "question": "How often did the obsolete memo require translation review?",
                        "answer": "Approved translations shall be reviewed every 24 months.",
                    },
                ],
            }
        ],
    },
]


def render_document(spec: dict, version: dict) -> str:
    metadata = {
        "Document Key": spec["document_key"],
        "Title": spec["title"],
        "Doc Type": spec["doc_type"],
        "Jurisdiction": spec["jurisdiction"],
        "Owner": spec["owner"],
        "Status": spec["status"],
        "Version Number": version["version_number"],
        "Effective Date": version["effective_date"],
    }
    header = "\n".join(f"{key}: {value}" for key, value in metadata.items())
    body = [
        f"# {spec['title']}",
        "",
        "## Purpose",
        version["purpose"],
        "",
        "## Controlled Requirements",
    ]
    for clause_index, clause in enumerate(version["clauses"], start=1):
        body.append(f"{clause_index}. {clause['answer']}")
    body.extend(
        [
            "",
            "## Compliance Notes",
            f"This {spec['doc_type']} applies to the {spec['jurisdiction']} controlled process area.",
            "This synthetic document is intended for retrieval, versioning, and audit traceability testing.",
        ]
    )
    return f"{header}\n\n" + "\n".join(body) + "\n"


def build_sheet_xml(headers: list[str], rows: list[list[object]]) -> str:
    def column_name(index: int) -> str:
        name = ""
        value = index + 1
        while value:
            value, remainder = divmod(value - 1, 26)
            name = chr(65 + remainder) + name
        return name

    def cell_xml(reference: str, value: object) -> str:
        if isinstance(value, (int, float)):
            return f'<c r="{reference}"><v>{value}</v></c>'
        return (
            f'<c r="{reference}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
        )

    all_rows = [headers] + rows
    row_xml: list[str] = []
    for row_index, row in enumerate(all_rows, start=1):
        cells = [
            cell_xml(f"{column_name(column_index)}{row_index}", value)
            for column_index, value in enumerate(row)
        ]
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        "</worksheet>"
    )


def write_xlsx(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    ensure_parent_dir(path)
    sheet_xml = build_sheet_xml(headers, rows)
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="document_register" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def generate_docs() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    headers = [
        "document_key",
        "title",
        "doc_type",
        "jurisdiction",
        "owner",
        "status",
        "version_number",
        "effective_date",
        "file_path",
    ]
    register_rows: list[list[object]] = []

    benchmark_rows: list[dict[str, str | int]] = []

    for spec in DOCUMENT_SPECS:
        expected_document_id = str(stable_uuid(f"{spec['document_key']}|document"))
        for version in spec["versions"]:
            file_name = f"{spec['document_key'].lower()}_v{version['version_number']}.md"
            relative_path = Path("data/docs") / file_name
            absolute_path = ROOT / relative_path
            ensure_parent_dir(absolute_path)
            absolute_path.write_text(render_document(spec, version), encoding="utf-8")
            register_rows.append(
                [
                    spec["document_key"],
                    spec["title"],
                    spec["doc_type"],
                    spec["jurisdiction"],
                    spec["owner"],
                    spec["status"],
                    version["version_number"],
                    version["effective_date"],
                    str(relative_path),
                ]
            )
            if spec["status"] == "APPROVED":
                for question_index, clause in enumerate(version["clauses"], start=1):
                    benchmark_rows.append(
                        {
                            "qid": f"{spec['document_key']}-v{version['version_number']}-q{question_index}",
                            "role": "Analyst",
                            "jurisdiction": spec["jurisdiction"],
                            "doc_type": spec["doc_type"],
                            "as_of": version["effective_date"],
                            "question": clause["question"],
                            "expected_document_id": expected_document_id,
                            "expected_version_number": version["version_number"],
                            "expected_phrase": clause["answer"],
                        }
                    )

    write_xlsx(REGISTER_PATH, headers, register_rows)
    ensure_parent_dir(BENCHMARK_PATH)
    BENCHMARK_PATH.write_text(
        "\n".join(json.dumps(row) for row in benchmark_rows[:60]) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    generate_docs()
