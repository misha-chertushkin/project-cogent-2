#!/usr/bin/env python3
"""
Generate synthetic PDF contracts for the Vendor Spend Analysis demo.

This script creates 20 PDF contracts with varying clauses to demonstrate
hybrid search capabilities. It includes a "trap" document for Apex Logistics
that has an expired termination date.
"""

import os
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


# Contract configurations - first 5 are high-value vendors (>$100M spend)
# We include variations in indemnification and warranty clauses
CONTRACT_CONFIGS = [
    # High-value vendors (>$100M) - 5 vendors
    {
        "vendor_name": "Premier Logistics Inc",
        "vendor_id": 3,
        "effective_date": "January 1, 2023",
        "termination_date": "December 1, 2025",
        "indemnification": "standard",
        "warranty": "standard",
        "is_trap": False,
    },
    {
        "vendor_name": "Precision Manufacturing",
        "vendor_id": 6,
        "effective_date": "March 15, 2023",
        "termination_date": "November 30, 2025",
        "indemnification": "enhanced",
        "warranty": "extended",
        "is_trap": False,
    },
    {
        "vendor_name": "Alpha Systems Inc",
        "vendor_id": 12,
        "effective_date": "June 1, 2023",
        "termination_date": "January 15, 2026",
        "indemnification": "missing",  # RISK: Missing indemnification
        "warranty": "standard",
        "is_trap": False,
    },
    {
        "vendor_name": "Zeta Corporation",
        "vendor_id": 18,
        "effective_date": "September 1, 2023",
        "termination_date": "December 20, 2025",
        "indemnification": "standard",
        "warranty": "missing",  # RISK: Missing warranty
        "is_trap": False,
    },
    {
        "vendor_name": "Quantum Dynamics",
        "vendor_id": 38,
        "effective_date": "April 1, 2023",
        "termination_date": "November 25, 2025",
        "indemnification": "risky",  # RISK: Risky indemnification clause
        "warranty": "limited",
        "is_trap": False,
    },
    # THE TRAP: Apex Logistics - contract EXPIRED but still shows as Active in DB
    {
        "vendor_name": "Apex Logistics",
        "vendor_id": 99,
        "effective_date": "January 1, 2022",
        "termination_date": "December 31, 2024",  # EXPIRED!
        "indemnification": "standard",
        "warranty": "standard",
        "is_trap": True,
        "is_confidential": True,
    },
    # Regular vendors with various clause variations
    {
        "vendor_name": "Acme Corporation",
        "vendor_id": 1,
        "effective_date": "February 1, 2023",
        "termination_date": "June 15, 2025",
        "indemnification": "standard",
        "warranty": "standard",
        "is_trap": False,
    },
    {
        "vendor_name": "Global Tech Solutions",
        "vendor_id": 2,
        "effective_date": "May 1, 2023",
        "termination_date": "September 30, 2025",
        "indemnification": "enhanced",
        "warranty": "extended",
        "is_trap": False,
    },
    {
        "vendor_name": "DataFlow Systems",
        "vendor_id": 4,
        "effective_date": "July 15, 2023",
        "termination_date": "March 15, 2025",
        "indemnification": "standard",
        "warranty": "standard",
        "is_trap": False,
    },
    {
        "vendor_name": "CloudNine Services",
        "vendor_id": 5,
        "effective_date": "August 1, 2023",
        "termination_date": "July 20, 2025",
        "indemnification": "missing",
        "warranty": "extended",
        "is_trap": False,
    },
    {
        "vendor_name": "NextGen Analytics",
        "vendor_id": 10,
        "effective_date": "October 1, 2023",
        "termination_date": "October 12, 2025",
        "indemnification": "standard",
        "warranty": "standard",
        "is_trap": False,
    },
    {
        "vendor_name": "Delta Logistics",
        "vendor_id": 15,
        "effective_date": "November 15, 2023",
        "termination_date": "September 5, 2025",
        "indemnification": "enhanced",
        "warranty": "missing",
        "is_trap": False,
    },
    {
        "vendor_name": "Kappa Industries",
        "vendor_id": 22,
        "effective_date": "December 1, 2023",
        "termination_date": "October 28, 2025",
        "indemnification": "risky",
        "warranty": "limited",
        "is_trap": False,
    },
    {
        "vendor_name": "Pi Manufacturing",
        "vendor_id": 28,
        "effective_date": "January 15, 2024",
        "termination_date": "November 8, 2025",
        "indemnification": "standard",
        "warranty": "standard",
        "is_trap": False,
    },
    {
        "vendor_name": "Upsilon Tech",
        "vendor_id": 32,
        "effective_date": "February 1, 2024",
        "termination_date": "October 15, 2025",
        "indemnification": "enhanced",
        "warranty": "extended",
        "is_trap": False,
    },
    {
        "vendor_name": "Cosmos Industries",
        "vendor_id": 41,
        "effective_date": "March 1, 2024",
        "termination_date": "October 2, 2025",
        "indemnification": "standard",
        "warranty": "standard",
        "is_trap": False,
    },
    {
        "vendor_name": "Orion Manufacturing",
        "vendor_id": 45,
        "effective_date": "April 1, 2024",
        "termination_date": "November 12, 2025",
        "indemnification": "missing",
        "warranty": "limited",
        "is_trap": False,
    },
    {
        "vendor_name": "Titan Corporation",
        "vendor_id": 49,
        "effective_date": "May 1, 2024",
        "termination_date": "October 20, 2025",
        "indemnification": "standard",
        "warranty": "standard",
        "is_trap": False,
    },
    {
        "vendor_name": "Stellar Systems",
        "vendor_id": 37,
        "effective_date": "June 1, 2024",
        "termination_date": "August 12, 2025",
        "indemnification": "risky",
        "warranty": "missing",
        "is_trap": False,
    },
    {
        "vendor_name": "Phoenix Solutions",
        "vendor_id": 48,
        "effective_date": "July 1, 2024",
        "termination_date": "September 8, 2025",
        "indemnification": "standard",
        "warranty": "extended",
        "is_trap": False,
    },
]


def get_indemnification_clause(clause_type: str) -> str:
    """Return indemnification clause based on type."""
    clauses = {
        "standard": """
        <b>8. INDEMNIFICATION</b><br/><br/>
        Vendor agrees to indemnify, defend, and hold harmless the Company, its officers,
        directors, employees, agents, and successors from and against any and all claims,
        damages, losses, costs, and expenses (including reasonable attorneys' fees) arising
        out of or relating to: (a) any breach of this Agreement by Vendor; (b) any negligent
        or wrongful act or omission of Vendor; (c) any violation of applicable laws by Vendor;
        or (d) any infringement of third-party intellectual property rights by Vendor's
        products or services.
        """,
        "enhanced": """
        <b>8. INDEMNIFICATION (ENHANCED)</b><br/><br/>
        Vendor agrees to provide comprehensive indemnification coverage as follows:<br/><br/>
        8.1 Vendor shall indemnify, defend, and hold harmless the Company from all claims,
        damages, and expenses arising from Vendor's performance under this Agreement.<br/><br/>
        8.2 This indemnification includes coverage for regulatory fines and penalties.<br/><br/>
        8.3 Vendor maintains minimum insurance coverage of $10,000,000 for such claims.<br/><br/>
        8.4 Indemnification obligations survive termination of this Agreement for five (5) years.
        """,
        "risky": """
        <b>8. LIMITED INDEMNIFICATION</b><br/><br/>
        Vendor's indemnification obligations are limited as follows: Vendor shall only
        indemnify Company for direct damages resulting from Vendor's gross negligence or
        willful misconduct, and in no event shall Vendor's total liability exceed the
        fees paid under this Agreement in the twelve (12) months preceding the claim.
        COMPANY ACKNOWLEDGES THIS LIMITED PROTECTION AND ACCEPTS ASSOCIATED RISKS.
        """,
        "missing": """
        <b>8. [SECTION RESERVED]</b><br/><br/>
        This section intentionally left blank. Parties to negotiate indemnification
        terms separately.
        """,
    }
    return clauses.get(clause_type, clauses["standard"])


def get_warranty_clause(clause_type: str) -> str:
    """Return warranty clause based on type."""
    clauses = {
        "standard": """
        <b>9. WARRANTIES</b><br/><br/>
        Vendor represents and warrants that: (a) it has full power and authority to enter
        into this Agreement; (b) all products and services provided will conform to
        specifications and be free from material defects; (c) all work will be performed
        in a professional and workmanlike manner; (d) products and services will not
        infringe any third-party rights; and (e) Vendor will comply with all applicable
        laws and regulations.
        """,
        "extended": """
        <b>9. EXTENDED WARRANTIES</b><br/><br/>
        In addition to standard warranties, Vendor provides the following extended protections:<br/><br/>
        9.1 All products carry a five (5) year warranty against defects.<br/><br/>
        9.2 Services include a satisfaction guarantee with full remediation rights.<br/><br/>
        9.3 Vendor warrants compliance with ISO 9001, SOC 2, and industry-specific standards.<br/><br/>
        9.4 Annual third-party audits will verify warranty compliance.
        """,
        "limited": """
        <b>9. LIMITED WARRANTY</b><br/><br/>
        VENDOR PROVIDES PRODUCTS AND SERVICES "AS IS" WITH LIMITED WARRANTY. Vendor
        warrants only that products will substantially conform to specifications for
        ninety (90) days. ALL OTHER WARRANTIES, EXPRESS OR IMPLIED, INCLUDING
        MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE DISCLAIMED.
        """,
        "missing": """
        <b>9. [WARRANTY TERMS PENDING]</b><br/><br/>
        Warranty terms to be established in a separate addendum. No warranties are
        provided under the terms of this master agreement.
        """,
    }
    return clauses.get(clause_type, clauses["standard"])


def create_contract_pdf(config: dict, output_dir: Path) -> str:
    """Create a single contract PDF."""
    vendor_name = config["vendor_name"]
    filename = f"{vendor_name.replace(' ', '_')}_MSA.pdf"
    filepath = output_dir / filename

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Center
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=20,
        spaceAfter=10,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=10,
    )
    confidential_style = ParagraphStyle(
        "Confidential",
        parent=styles["Normal"],
        fontSize=14,
        textColor="red",
        alignment=1,
        spaceBefore=0,
        spaceAfter=20,
    )

    story = []

    # Add CONFIDENTIAL watermark for trap document
    if config.get("is_confidential"):
        story.append(
            Paragraph("*** CONFIDENTIAL ***", confidential_style)
        )

    # Title
    story.append(
        Paragraph(
            f"MASTER SERVICE AGREEMENT<br/>{vendor_name}",
            title_style,
        )
    )

    story.append(Spacer(1, 20))

    # Preamble
    preamble = f"""
    This Master Service Agreement ("Agreement") is entered into as of {config['effective_date']}
    ("Effective Date") by and between:<br/><br/>
    <b>COMPANY:</b> Enterprise Corporation ("Company")<br/>
    <b>VENDOR:</b> {vendor_name} ("Vendor")<br/><br/>
    Vendor ID: {config['vendor_id']}
    """
    story.append(Paragraph(preamble, body_style))

    story.append(Spacer(1, 15))

    # Standard sections
    sections = [
        (
            "1. SCOPE OF SERVICES",
            """Vendor agrees to provide products and/or services as described in
            individual Statements of Work (SOW) executed under this Agreement. Each SOW
            shall reference this Agreement and be subject to its terms and conditions.""",
        ),
        (
            "2. TERM AND TERMINATION",
            f"""<b>Term:</b> This Agreement shall commence on the Effective Date and
            continue until <b>{config['termination_date']}</b> ("Term"), unless earlier
            terminated as provided herein.<br/><br/>
            <b>Termination for Convenience:</b> Either party may terminate this Agreement
            upon ninety (90) days written notice.<br/><br/>
            <b>Termination for Cause:</b> Either party may terminate immediately upon
            material breach that remains uncured for thirty (30) days after notice.<br/><br/>
            <b>IMPORTANT: This agreement shall terminate automatically on {config['termination_date']}.</b>""",
        ),
        (
            "3. COMPENSATION",
            """Company shall pay Vendor in accordance with the pricing terms set forth
            in each SOW. Payment terms are Net 30 from receipt of valid invoice. Vendor
            shall submit itemized invoices monthly.""",
        ),
        (
            "4. CONFIDENTIALITY",
            """Each party agrees to maintain in confidence all Confidential Information
            of the other party. "Confidential Information" means any non-public information
            disclosed by either party that is designated as confidential or that reasonably
            should be understood to be confidential.""",
        ),
        (
            "5. INTELLECTUAL PROPERTY",
            """All pre-existing intellectual property remains the property of the
            disclosing party. Work product created specifically for Company under this
            Agreement shall be owned by Company upon full payment.""",
        ),
        (
            "6. DATA PROTECTION",
            """Vendor shall comply with all applicable data protection laws and
            regulations, including GDPR and CCPA where applicable. Vendor shall implement
            appropriate technical and organizational measures to protect personal data.""",
        ),
        (
            "7. INSURANCE",
            """Vendor shall maintain: (a) Commercial General Liability of at least
            $1,000,000 per occurrence; (b) Professional Liability of at least $2,000,000;
            (c) Workers' Compensation as required by law.""",
        ),
    ]

    for title, content in sections:
        story.append(Paragraph(f"<b>{title}</b>", heading_style))
        story.append(Paragraph(content, body_style))

    # Indemnification clause (varies)
    story.append(
        Paragraph(
            get_indemnification_clause(config["indemnification"]),
            body_style,
        )
    )

    # Warranty clause (varies)
    story.append(
        Paragraph(
            get_warranty_clause(config["warranty"]),
            body_style,
        )
    )

    # Additional standard sections
    additional_sections = [
        (
            "10. LIMITATION OF LIABILITY",
            """EXCEPT FOR BREACHES OF CONFIDENTIALITY OR INDEMNIFICATION OBLIGATIONS,
            NEITHER PARTY SHALL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
            CONSEQUENTIAL, OR PUNITIVE DAMAGES.""",
        ),
        (
            "11. GOVERNING LAW",
            """This Agreement shall be governed by and construed in accordance with
            the laws of the State of Delaware, without regard to conflict of law principles.""",
        ),
        (
            "12. DISPUTE RESOLUTION",
            """Any dispute arising under this Agreement shall first be subject to
            good faith negotiation. If unresolved within thirty (30) days, disputes
            shall be submitted to binding arbitration under AAA Commercial Rules.""",
        ),
        (
            "13. ENTIRE AGREEMENT",
            """This Agreement, together with all SOWs and attachments, constitutes
            the entire agreement between the parties and supersedes all prior agreements
            and understandings.""",
        ),
    ]

    for title, content in additional_sections:
        story.append(Paragraph(f"<b>{title}</b>", heading_style))
        story.append(Paragraph(content, body_style))

    story.append(Spacer(1, 30))

    # Signature block
    signature = """
    <b>IN WITNESS WHEREOF</b>, the parties have executed this Agreement as of the
    Effective Date.<br/><br/>
    <b>COMPANY:</b> Enterprise Corporation<br/>
    By: _______________________________<br/>
    Name: [Authorized Signatory]<br/>
    Title: Chief Procurement Officer<br/>
    Date: _______________________________<br/><br/>
    <b>VENDOR:</b> {vendor}<br/>
    By: _______________________________<br/>
    Name: [Authorized Signatory]<br/>
    Title: _______________________________<br/>
    Date: _______________________________
    """.format(vendor=vendor_name)
    story.append(Paragraph(signature, body_style))

    # Build PDF
    doc.build(story)

    return filename


def main():
    """Generate all contract PDFs."""
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "data" / "contracts"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(CONTRACT_CONFIGS)} contract PDFs...")
    print(f"Output directory: {output_dir}")
    print("-" * 50)

    for config in CONTRACT_CONFIGS:
        filename = create_contract_pdf(config, output_dir)
        trap_indicator = " [TRAP - EXPIRED CONTRACT]" if config["is_trap"] else ""
        risk_indicators = []
        if config["indemnification"] in ["missing", "risky"]:
            risk_indicators.append(f"Indemnification: {config['indemnification']}")
        if config["warranty"] in ["missing", "limited"]:
            risk_indicators.append(f"Warranty: {config['warranty']}")

        risk_str = f" [RISKS: {', '.join(risk_indicators)}]" if risk_indicators else ""
        print(f"  Created: {filename}{trap_indicator}{risk_str}")

    print("-" * 50)
    print(f"Successfully generated {len(CONTRACT_CONFIGS)} contracts.")
    print("\nKey documents for demo:")
    print("  - High-value vendors (>$100M): Premier Logistics, Precision Manufacturing,")
    print("    Alpha Systems, Zeta Corporation, Quantum Dynamics, Apex Logistics")
    print("  - TRAP document: Apex_Logistics_MSA.pdf (expired Dec 31, 2024)")
    print("  - Missing indemnification: Alpha Systems, CloudNine, Orion")
    print("  - Risky indemnification: Quantum Dynamics, Kappa Industries, Stellar")


if __name__ == "__main__":
    main()
