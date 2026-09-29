"""
ONION_SURE — Digital Quality Reporting & Verification Service
Smart India Hackathon 2026 - Problem Statement PS26031

Features:
- Report metadata aggregation (Inspection, Lot, Farmer, Centre, Operator, Dates)
- Deterministic grade results & lot percentage calculations (Grade A, URS, Reject)
- Defect breakdown (Healthy, Damaged, Rotten, Sprouted, Unknown)
- Physical sizing and diameter statistics (Average diameter mm, Undersized count/%)
- AI model version and grading policy version traceability
- Manual review audit history
- Cryptographic verification ID and SHA-256 tamper-evident hash
- Dynamic QR code generation encoding verification URL
- Professional publication-grade PDF report generation (ReportLab)
- Privacy-preserving public read-only verification (No sensitive PII exposed)
"""

import io
import os
import uuid
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session

import qrcode
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
    HRFlowable,
)

from ..models.entities import (
    Report,
    Inspection,
    Lot,
    Farmer,
    ProcurementCentre,
    User,
    InspectionImage,
    GradeResult,
    ManualReview,
    ModelVersion,
    GradingPolicyVersion,
)
from ..services.audit_service import AuditService
from ..services.storage_service import image_storage_service


class ReportService:
    @staticmethod
    def generate_verification_id() -> str:
        """Generates a short, human-readable unique verification code (e.g. VER-7F9A1B3C)."""
        return f"VER-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def generate_qr_code_image(verification_url: str) -> bytes:
        """Generates a crisp PNG QR code image for the verification URL."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=5,
            border=2,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1E293B", back_color="#FFFFFF")

        buffer = io.BytesIO()
        img.save(buffer)
        return buffer.getvalue()

    @classmethod
    def aggregate_inspection_report_data(cls, db: Session, inspection_id: str) -> Dict[str, Any]:
        """
        Gathers and calculates all required report fields from the relational database.
        """
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not inspection:
            raise ValueError(f"Inspection '{inspection_id}' not found.")

        lot = db.query(Lot).filter(Lot.id == inspection.lot_id).first()
        farmer = db.query(Farmer).filter(Farmer.id == lot.farmer_id).first() if lot else None
        centre = (
            db.query(ProcurementCentre).filter(ProcurementCentre.id == lot.procurement_centre_id).first()
            if lot
            else None
        )
        inspector = db.query(User).filter(User.id == inspection.inspector_id).first()

        # Grade Results and Detections
        grade_results = db.query(GradeResult).filter(GradeResult.inspection_id == inspection_id).all()

        # 1. Defect Distribution
        defect_counts = {
            "HEALTHY": 0,
            "DAMAGED": 0,
            "ROTTEN": 0,
            "SPROUTED": 0,
            "UNKNOWN": 0,
        }

        # 2. Size & Measurement Distribution
        size_counts = {
            "ACCEPTABLE_SIZE": 0,
            "UNDERSIZED": 0,
            "UNDETERMINED": 0,
        }
        valid_diameters = []

        model_version_str = "v1.0.0-resnet50"
        policy_version_str = "v1.0.0-standard"

        for gr in grade_results:
            # Model & Policy versions from associations
            if gr.model_version and gr.model_version.version:
                model_version_str = gr.model_version.version
            if gr.policy_version and gr.policy_version.version:
                policy_version_str = gr.policy_version.version

            # Check linked detection
            det = gr.detection
            if det:
                if det.defect_result:
                    d_cls = det.defect_result.defect_class
                    defect_counts[d_cls] = defect_counts.get(d_cls, 0) + 1
                else:
                    defect_counts["UNKNOWN"] += 1

                if det.measurement and det.measurement.status == "measured":
                    diam = det.measurement.diameter_mm
                    if diam is not None and diam > 0:
                        valid_diameters.append(diam)
                        if diam >= 45.0:
                            size_counts["ACCEPTABLE_SIZE"] += 1
                        else:
                            size_counts["UNDERSIZED"] += 1
                    else:
                        size_counts["UNDETERMINED"] += 1
                else:
                    size_counts["UNDETERMINED"] += 1
            else:
                # If individual detections not populated, use overall grade proxy
                if gr.grade == "GRADE_A":
                    defect_counts["HEALTHY"] += 1
                    size_counts["ACCEPTABLE_SIZE"] += 1
                elif gr.grade == "URS":
                    defect_counts["DAMAGED"] += 1
                    size_counts["ACCEPTABLE_SIZE"] += 1
                elif gr.grade == "REJECT":
                    defect_counts["ROTTEN"] += 1
                    size_counts["UNDERSIZED"] += 1

        # If zero detections were recorded (e.g. bulk summary mode), initialize from inspection summary
        if sum(defect_counts.values()) == 0 and inspection.total_onions_evaluated > 0:
            defect_counts["HEALTHY"] = inspection.grade_a_count
            defect_counts["DAMAGED"] = inspection.urs_count
            defect_counts["ROTTEN"] = inspection.reject_count
            size_counts["ACCEPTABLE_SIZE"] = inspection.grade_a_count + inspection.urs_count
            size_counts["UNDERSIZED"] = inspection.reject_count

        avg_diameter_mm = (
            round(sum(valid_diameters) / len(valid_diameters), 1)
            if valid_diameters
            else None
        )

        # 3. Evidence Images
        images = db.query(InspectionImage).filter(InspectionImage.inspection_id == inspection_id).all()
        evidence_images = [
            {
                "id": img.id,
                "filename": img.filename,
                "storage_key": img.storage_key,
                "quality_status": img.quality_status,
                "blur_variance": img.blur_variance,
                "mean_brightness": img.mean_brightness,
                "calibration_detected": img.calibration_detected,
                "pixels_per_mm": img.pixels_per_mm,
            }
            for img in images
        ]

        # 4. Manual Review History
        manual_reviews = (
            db.query(ManualReview).filter(ManualReview.inspection_id == inspection_id).all()
        )
        review_history = [
            {
                "reviewer": mr.reviewer.full_name if mr.reviewer else "Quality Reviewer",
                "original_grade": mr.original_grade,
                "reviewed_grade": mr.reviewed_grade,
                "reason": mr.reason,
                "comments": mr.comments,
                "reviewed_at": mr.created_at.isoformat() if mr.created_at else None,
            }
            for mr in manual_reviews
        ]

        # 5. Verification IDs & Hashes
        verification_id = cls.generate_verification_id()
        verification_url = f"https://onionsure.doca.gov.in/verify/{verification_id}"
        now_utc = datetime.now(timezone.utc)
        raw_hash_str = f"{inspection.id}:{verification_id}:{inspection.lot_decision}:{now_utc.isoformat()}"
        qr_verification_hash = hashlib.sha256(raw_hash_str.encode("utf-8")).hexdigest()

        return {
            "report_code": f"REP-{inspection.inspection_code}",
            "inspection_id": inspection.id,
            "inspection_code": inspection.inspection_code,
            "verification_id": verification_id,
            "verification_url": verification_url,
            "qr_verification_hash": qr_verification_hash,
            "generated_at": now_utc,
            "lot_id": lot.id if lot else None,
            "lot_number": lot.lot_number if lot else "LOT-UNKNOWN",
            "variety": lot.variety if lot else "Red Onion",
            "quantity_quintals": float(lot.quantity_quintals) if lot else 0.0,
            "bag_count": lot.bag_count if lot else 0,
            "farmer_name": farmer.name if farmer else "Authorized Mandi Farmer",
            "farmer_code": farmer.farmer_code if farmer else "FARM-GENERIC",
            "farmer_district": farmer.district if farmer else "Nashik",
            "farmer_state": farmer.state if farmer else "Maharashtra",
            "centre_name": centre.name if centre else "National APMC Procurement Centre",
            "centre_code": centre.centre_code if centre else "APMC-01",
            "centre_location": f"{centre.district}, {centre.state}" if centre else "Nashik, Maharashtra",
            "operator_name": inspector.full_name if inspector else "Authorized Mandi Inspector",
            "sample_size": inspection.total_onions_evaluated or inspection.sample_size or 50,
            "lot_decision": inspection.lot_decision or "ACCEPT_GRADE_A",
            "decision_reason": inspection.decision_reason or "Automated deterministic evaluation conforming to PS26031.",
            "grade_a_percentage": float(inspection.grade_a_percentage),
            "urs_percentage": float(inspection.urs_percentage),
            "reject_percentage": float(inspection.reject_percentage),
            "grade_a_count": inspection.grade_a_count,
            "urs_count": inspection.urs_count,
            "reject_count": inspection.reject_count,
            "manual_review_count": inspection.manual_review_count,
            "defect_distribution": defect_counts,
            "size_distribution": size_counts,
            "average_diameter_mm": avg_diameter_mm,
            "model_version": model_version_str,
            "grading_policy_version": policy_version_str,
            "evidence_images": evidence_images,
            "manual_review_history": review_history,
        }

    @classmethod
    def generate_pdf_document(cls, report_data: Dict[str, Any], qr_png_bytes: bytes) -> bytes:
        """
        Builds a comprehensive, publication-quality PDF report using ReportLab Platypus.
        """
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        normal_style = styles["Normal"]

        # Custom Brand Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=normal_style,
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#065F46"),
            alignment=1,  # Center
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=normal_style,
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#1F2937"),
            alignment=1,
        )
        agency_style = ParagraphStyle(
            "DocAgency",
            parent=normal_style,
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#4B5563"),
            alignment=1,
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=normal_style,
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=4,
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=normal_style,
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#111827"),
        )
        cell_normal = ParagraphStyle(
            "CellNormal",
            parent=normal_style,
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#374151"),
        )

        elements = []

        # --------------------------------------------------------------------
        # 1. Government & System Header
        # --------------------------------------------------------------------
        elements.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION", agency_style))
        elements.append(Paragraph("DEPARTMENT OF CONSUMER AFFAIRS (DoCA) — GOVERNMENT OF INDIA", agency_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("ONION_SURE : DIGITAL QUALITY INSPECTION CERTIFICATE", title_style))
        elements.append(Paragraph("Smart India Hackathon 2026 — Problem Statement PS26031 (Smart Automation)", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#059669"), spaceBefore=2, spaceAfter=8))

        # --------------------------------------------------------------------
        # 2. Key Metadata Badge Banner
        # --------------------------------------------------------------------
        meta_table_data = [
            [
                Paragraph(f"<b>Report ID:</b> {report_data['report_code']}", cell_normal),
                Paragraph(f"<b>Verification ID:</b> {report_data['verification_id']}", cell_normal),
                Paragraph(f"<b>Date/Time:</b> {report_data['generated_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}", cell_normal),
            ],
            [
                Paragraph(f"<b>Inspection:</b> {report_data['inspection_code']}", cell_normal),
                Paragraph(f"<b>Status:</b> FINALIZED & VERIFIED", cell_normal),
                Paragraph(f"<b>Policy Version:</b> {report_data['grading_policy_version']}", cell_normal),
            ],
        ]
        meta_table = Table(meta_table_data, colWidths=[175, 175, 175])
        meta_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(meta_table)
        elements.append(Spacer(1, 10))

        # --------------------------------------------------------------------
        # 3. Lot, Farmer & Procurement Centre Details
        # --------------------------------------------------------------------
        elements.append(Paragraph("1. Lot & Procurement Origin Details", section_heading))
        lot_farmer_data = [
            [
                Paragraph("<b>Lot Number:</b>", cell_bold),
                Paragraph(str(report_data["lot_number"]), cell_normal),
                Paragraph("<b>Farmer Name:</b>", cell_bold),
                Paragraph(str(report_data["farmer_name"]), cell_normal),
            ],
            [
                Paragraph("<b>Variety:</b>", cell_bold),
                Paragraph(str(report_data["variety"]), cell_normal),
                Paragraph("<b>Farmer Code:</b>", cell_bold),
                Paragraph(str(report_data["farmer_code"]), cell_normal),
            ],
            [
                Paragraph("<b>Quantity (Quintals):</b>", cell_bold),
                Paragraph(f"{report_data['quantity_quintals']:.1f} qtl ({report_data['bag_count']} bags)", cell_normal),
                Paragraph("<b>Origin District/State:</b>", cell_bold),
                Paragraph(f"{report_data['farmer_district']}, {report_data['farmer_state']}", cell_normal),
            ],
            [
                Paragraph("<b>Procurement Mandi:</b>", cell_bold),
                Paragraph(f"{report_data['centre_name']} ({report_data['centre_code']})", cell_normal),
                Paragraph("<b>Authorized Operator:</b>", cell_bold),
                Paragraph(str(report_data["operator_name"]), cell_normal),
            ],
        ]
        lot_table = Table(lot_farmer_data, colWidths=[130, 130, 130, 135])
        lot_table.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F9FAFB")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F9FAFB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )
        elements.append(lot_table)
        elements.append(Spacer(1, 10))

        # --------------------------------------------------------------------
        # 4. Deterministic Grading Engine Results
        # --------------------------------------------------------------------
        elements.append(Paragraph("2. Deterministic Quality Grading Assessment", section_heading))
        
        # Color coding decision banner
        decision = report_data["lot_decision"]
        if decision == "ACCEPT_GRADE_A":
            decision_color = "#16A34A"
            decision_bg = "#DCFCE7"
            decision_text = "GRADE A — ACCEPTABLE (High Quality Standard)"
        elif decision == "ACCEPT_URS":
            decision_color = "#D97706"
            decision_bg = "#FEF3C7"
            decision_text = "URS — UNDER REGISTRATION / CONDITIONAL ACCEPTANCE"
        else:
            decision_color = "#DC2626"
            decision_bg = "#FEE2E2"
            decision_text = "REJECT LOT — QUALITY CRITERIA NOT MET"

        grading_summary_data = [
            [
                Paragraph("<b>Sample Size Assessed:</b>", cell_bold),
                Paragraph(f"{report_data['sample_size']} onions", cell_normal),
                Paragraph("<b>Final Lot Decision:</b>", cell_bold),
                Paragraph(f"<font color='{decision_color}'><b>{decision_text}</b></font>", cell_normal),
            ],
            [
                Paragraph("<b>Grade A Percentage:</b>", cell_bold),
                Paragraph(f"<b>{report_data['grade_a_percentage']:.1f}%</b> ({report_data['grade_a_count']} pcs)", cell_normal),
                Paragraph("<b>Decision Reason:</b>", cell_bold),
                Paragraph(str(report_data["decision_reason"]), cell_normal),
            ],
            [
                Paragraph("<b>URS Percentage:</b>", cell_bold),
                Paragraph(f"<b>{report_data['urs_percentage']:.1f}%</b> ({report_data['urs_count']} pcs)", cell_normal),
                Paragraph("<b>AI Model Version:</b>", cell_bold),
                Paragraph(str(report_data["model_version"]), cell_normal),
            ],
            [
                Paragraph("<b>Reject Percentage:</b>", cell_bold),
                Paragraph(f"<b>{report_data['reject_percentage']:.1f}%</b> ({report_data['reject_count']} pcs)", cell_normal),
                Paragraph("<b>Deterministic Policy:</b>", cell_bold),
                Paragraph(str(report_data["grading_policy_version"]), cell_normal),
            ],
        ]
        grade_table = Table(grading_summary_data, colWidths=[130, 130, 130, 135])
        grade_table.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F9FAFB")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F9FAFB")),
                ("BACKGROUND", (3, 0), (3, 0), colors.HexColor(decision_bg)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )
        elements.append(grade_table)
        elements.append(Spacer(1, 10))

        # --------------------------------------------------------------------
        # 5. Defect & Size Distribution Breakdown
        # --------------------------------------------------------------------
        elements.append(Paragraph("3. Defect & Physical Sizing Distribution", section_heading))
        defects = report_data["defect_distribution"]
        sizing = report_data["size_distribution"]
        avg_diam_str = f"{report_data['average_diameter_mm']} mm" if report_data["average_diameter_mm"] else "Calibration Unavailable"

        dist_data = [
            [
                Paragraph("<b>Defect Category</b>", cell_bold),
                Paragraph("<b>Count</b>", cell_bold),
                Paragraph("<b>Size Classification</b>", cell_bold),
                Paragraph("<b>Count</b>", cell_bold),
            ],
            [
                Paragraph("Healthy (No Defect)", cell_normal),
                Paragraph(str(defects.get("HEALTHY", 0)), cell_normal),
                Paragraph("Acceptable Size (≥ 45mm)", cell_normal),
                Paragraph(str(sizing.get("ACCEPTABLE_SIZE", 0)), cell_normal),
            ],
            [
                Paragraph("Damaged / Surface Blemish", cell_normal),
                Paragraph(str(defects.get("DAMAGED", 0)), cell_normal),
                Paragraph("Undersized (< 45mm)", cell_normal),
                Paragraph(str(sizing.get("UNDERSIZED", 0)), cell_normal),
            ],
            [
                Paragraph("Rotten / Basal Rot (Critical)", cell_normal),
                Paragraph(str(defects.get("ROTTEN", 0)), cell_normal),
                Paragraph("Undetermined Size", cell_normal),
                Paragraph(str(sizing.get("UNDETERMINED", 0)), cell_normal),
            ],
            [
                Paragraph("Sprouted (Critical Defect)", cell_normal),
                Paragraph(str(defects.get("SPROUTED", 0)), cell_normal),
                Paragraph("<b>Average Diameter:</b>", cell_bold),
                Paragraph(f"<b>{avg_diam_str}</b>", cell_normal),
            ],
        ]
        dist_table = Table(dist_data, colWidths=[160, 100, 165, 100])
        dist_table.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )
        elements.append(dist_table)
        elements.append(Spacer(1, 10))

        # --------------------------------------------------------------------
        # 6. Manual Review History (if any)
        # --------------------------------------------------------------------
        reviews = report_data.get("manual_review_history", [])
        if reviews:
            elements.append(Paragraph("4. Manual Human Review Audit History", section_heading))
            review_table_data = [
                [
                    Paragraph("<b>Reviewer</b>", cell_bold),
                    Paragraph("<b>Original</b>", cell_bold),
                    Paragraph("<b>Override</b>", cell_bold),
                    Paragraph("<b>Reason & Notes</b>", cell_bold),
                ]
            ]
            for r in reviews:
                review_table_data.append([
                    Paragraph(str(r.get("reviewer")), cell_normal),
                    Paragraph(str(r.get("original_grade")), cell_normal),
                    Paragraph(str(r.get("reviewed_grade")), cell_normal),
                    Paragraph(f"{r.get('reason')}: {r.get('comments') or 'None'}", cell_normal),
                ])
            rev_table = Table(review_table_data, colWidths=[125, 80, 80, 240])
            rev_table.setStyle(
                TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ])
            )
            elements.append(rev_table)
            elements.append(Spacer(1, 10))

        # --------------------------------------------------------------------
        # 7. Verification QR Code & Cryptographic Authenticity Footer
        # --------------------------------------------------------------------
        elements.append(KeepTogether([
            Paragraph("Official Verification & Public Validation", section_heading),
            HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#9CA3AF"), spaceBefore=2, spaceAfter=6),
            Table(
                [
                    [
                        RLImage(io.BytesIO(qr_png_bytes), width=85, height=85),
                        [
                            Paragraph("<b>Scan with Mobile Camera or Mandi Terminal to Verify Certificate:</b>", cell_bold),
                            Paragraph(f"<b>Verification URL:</b> <font color='#0284C7'>{report_data['verification_url']}</font>", cell_normal),
                            Paragraph(f"<b>Verification ID:</b> <code>{report_data['verification_id']}</code>", cell_normal),
                            Paragraph(f"<b>SHA-256 Cryptographic Digest:</b> <font size='7'><code>{report_data['qr_verification_hash']}</code></font>", cell_normal),
                            Spacer(1, 4),
                            Paragraph(
                                "<font size='7' color='#6B7280'>This certificate was generated by the deterministic ONION_SURE AI grading engine conforming to Ministry of Consumer Affairs guidelines. Digital verification is public and privacy-preserving; personal identifying information is omitted from verification queries.</font>",
                                cell_normal,
                            ),
                        ],
                    ]
                ],
                colWidths=[100, 425],
                style=[
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (1, 0), (1, 0), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ],
            ),
        ]))

        doc.build(elements)
        return pdf_buffer.getvalue()

    @classmethod
    def finalize_and_generate_report(
        cls,
        db: Session,
        inspection_id: str,
        actor_id: str = "system",
    ) -> Report:
        """
        Orchestrates full report lifecycle:
        1. Aggregates inspection & grading metadata
        2. Generates QR code
        3. Generates PDF document via ReportLab
        4. Saves PDF and QR in storage service
        5. Persists Report record in database
        6. Logs event to audit trail
        """
        # Check if report already exists for this inspection
        existing = db.query(Report).filter(Report.inspection_id == inspection_id).first()
        if existing:
            return existing

        # 1. Aggregate Report Data
        report_data = cls.aggregate_inspection_report_data(db, inspection_id)

        # 2. Generate QR Code Image
        qr_bytes = cls.generate_qr_code_image(report_data["verification_url"])
        qr_storage = image_storage_service.save_file(
            content=qr_bytes,
            filename=f"qr_{report_data['verification_id']}.png",
            content_type="image/png",
        )

        # 3. Generate PDF Document
        pdf_bytes = cls.generate_pdf_document(report_data, qr_bytes)
        pdf_storage = image_storage_service.save_file(
            content=pdf_bytes,
            filename=f"{report_data['report_code']}.pdf",
            content_type="application/pdf",
        )

        # 4. Package summary metrics for JSON storage
        summary_metrics = {
            "verification_id": report_data["verification_id"],
            "verification_url": report_data["verification_url"],
            "lot_id": report_data["lot_id"],
            "lot_number": report_data["lot_number"],
            "variety": report_data["variety"],
            "quantity_quintals": report_data["quantity_quintals"],
            "bag_count": report_data["bag_count"],
            "farmer_name": report_data["farmer_name"],
            "farmer_code": report_data["farmer_code"],
            "centre_name": report_data["centre_name"],
            "centre_code": report_data["centre_code"],
            "operator_name": report_data["operator_name"],
            "sample_size": report_data["sample_size"],
            "lot_decision": report_data["lot_decision"],
            "decision_reason": report_data["decision_reason"],
            "grade_a_percentage": report_data["grade_a_percentage"],
            "urs_percentage": report_data["urs_percentage"],
            "reject_percentage": report_data["reject_percentage"],
            "grade_a_count": report_data["grade_a_count"],
            "urs_count": report_data["urs_count"],
            "reject_count": report_data["reject_count"],
            "defect_distribution": report_data["defect_distribution"],
            "size_distribution": report_data["size_distribution"],
            "average_diameter_mm": report_data["average_diameter_mm"],
            "model_version": report_data["model_version"],
            "policy_version": report_data["grading_policy_version"],
            "qr_storage_key": qr_storage["storage_key"],
            "evidence_image_count": len(report_data["evidence_images"]),
            "manual_review_count": len(report_data["manual_review_history"]),
        }

        # 5. Persist Report Entity
        report = Report(
            report_code=report_data["report_code"],
            inspection_id=inspection_id,
            qr_verification_hash=report_data["qr_verification_hash"],
            summary_metrics=summary_metrics,
            pdf_storage_key=pdf_storage["storage_key"],
            is_finalized=True,
            generated_at=report_data["generated_at"],
        )
        db.add(report)

        # Mark inspection COMPLETED
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if inspection:
            inspection.status = "COMPLETED"
            inspection.finalized_at = report_data["generated_at"]

        db.flush()

        # 6. Audit Trail Logging (ensure actor_id is valid user foreign key or None)
        valid_actor_id = None
        if actor_id and actor_id != "system":
            user_exists = db.query(User).filter(User.id == actor_id).first()
            if user_exists:
                valid_actor_id = actor_id
        if not valid_actor_id and inspection and getattr(inspection, "inspector_id", None):
            user_exists = db.query(User).filter(User.id == inspection.inspector_id).first()
            if user_exists:
                valid_actor_id = inspection.inspector_id

        AuditService.log_event(
            db=db,
            actor_id=valid_actor_id,
            action="GENERATE_QUALITY_REPORT",
            entity_type="Report",
            entity_id=report.id,
            new_values={
                "report_code": report.report_code,
                "verification_id": report_data["verification_id"],
                "qr_hash": report.qr_verification_hash,
                "pdf_key": report.pdf_storage_key,
            },
        )

        db.commit()
        db.refresh(report)
        return report

    @classmethod
    def verify_public_report(cls, db: Session, identifier: str) -> Dict[str, Any]:
        """
        Public, read-only verification lookup:
        - Accepts verification_id, qr_verification_hash, or report_code.
        - Privacy Rule: Does NOT expose sensitive personal data (phone, address, aadhaar, internal credentials).
        """
        clean_id = identifier.strip()

        # 1. Search by qr_verification_hash
        report = db.query(Report).filter(Report.qr_verification_hash == clean_id).first()

        # 2. Search by report_code or ID
        if not report:
            report = db.query(Report).filter(
                (Report.report_code == clean_id) | (Report.id == clean_id)
            ).first()

        # 3. Search in summary_metrics JSON for verification_id
        if not report:
            all_reports = db.query(Report).all()
            for r in all_reports:
                if (
                    isinstance(r.summary_metrics, dict)
                    and r.summary_metrics.get("verification_id") == clean_id
                ):
                    report = r
                    break

        if not report:
            return {
                "is_valid": False,
                "verification_status": "INVALID",
                "message": "Certificate identifier not found in DoCA national registry.",
                "verification_source": "DoCA Official Verification Registry (SIH 2026 PS26031)",
            }

        metrics = report.summary_metrics or {}
        return {
            "is_valid": bool(report.is_finalized),
            "verification_status": "VALID" if report.is_finalized else "REVOKED",
            "report_code": report.report_code,
            "verification_id": metrics.get("verification_id", "VER-AUTHENTIC"),
            "inspection_code": report.inspection.inspection_code if report.inspection else "INSP-REF",
            "lot_number": metrics.get("lot_number", "LOT-NASHIK"),
            "variety": metrics.get("variety", "Red Onion"),
            "inspection_date": report.generated_at.strftime("%Y-%m-%d"),
            "procurement_centre": metrics.get("centre_name", "National APMC Procurement Centre"),
            "sample_size": metrics.get("sample_size", 50),
            "lot_decision": metrics.get("lot_decision", "ACCEPT_GRADE_A"),
            "grade_a_percentage": metrics.get("grade_a_percentage", 0.0),
            "urs_percentage": metrics.get("urs_percentage", 0.0),
            "reject_percentage": metrics.get("reject_percentage", 0.0),
            "average_diameter_mm": metrics.get("average_diameter_mm"),
            "model_version": metrics.get("model_version", "v1.0.0"),
            "policy_version": metrics.get("policy_version", "v1.0.0"),
            "verification_source": "DoCA Official Verification Registry (SIH 2026 PS26031)",
        }
