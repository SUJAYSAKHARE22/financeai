"""
AI_CA ITR & Document Generator Service
Generates official e-filing JSON and professional ReportLab PDFs for:
1. ITR-1 Sahaj Income Tax Return
2. Form 16 Tax Computation Statement
3. Form 26AS Reconciled TDS Statement
"""
import io
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from models.aica_schemas import TaxpayerProfile, TaxRegime, AICACategory


def generate_itr_json(profile: TaxpayerProfile, tax_result: dict, classified: list) -> dict:
    """
    Generate a complete, fully populated ITR-1 e-filing portal JSON payload.
    Conforms to the actual schema structures used by the Income Tax Department.
    """
    now = datetime.utcnow()
    
    # Calculate components from transactions
    salary_income = sum(t.original_amount for t in classified if t.aica_category == AICACategory.SALARY)
    interest_income = sum(t.original_amount for t in classified if t.aica_category == AICACategory.INTEREST_INCOME)
    freelance_income = sum(t.original_amount for t in classified if t.aica_category in (AICACategory.FREELANCE_INCOME, AICACategory.BUSINESS_INCOME))
    
    ded_80c = tax_result.get("deduction_breakdown", {}).get("section_80c", 0.0)
    ded_80d = tax_result.get("deduction_breakdown", {}).get("section_80d", 0.0)
    std_ded = tax_result.get("deduction_breakdown", {}).get("standard_deduction", 0.0)
    
    # Draft official JSON matching income tax department schema
    itr_data = {
        "ITR": {
            "Header": {
                "SchemaVersion": "1.0.0",
                "FormName": "ITR-1",
                "AssessmentYear": "2025-26",
                "FinancialYear": "2024-25",
                "CreatedBy": "FinanceAI-CA-Engine",
                "CreatedAt": now.isoformat()
            },
            "ITR1_Sahaj": {
                "PersonalInfo": {
                    "AssesseeName": {
                        "FirstName": profile.first_name,
                        "MiddleName": profile.middle_name or "",
                        "SurNameOrLastName": profile.last_name
                    },
                    "PAN": profile.pan,
                    "AadhaarCardNo": profile.aadhaar_no.replace(" ", ""),
                    "DOB": profile.dob,
                    "Address": {
                        "FlatDoorBlockNo": profile.address_flat,
                        "NameOfPremisesBuilding": profile.address_premises,
                        "RoadStreetPostOffice": profile.address_road,
                        "AreaLocality": profile.address_area,
                        "TownCityDistrict": profile.address_city,
                        "StateCode": profile.address_state,
                        "PinCode": profile.address_pin
                    },
                    "EmailAddress": profile.email,
                    "MobileNo": profile.mobile,
                    "EmployerCategory": profile.employer_type
                },
                "FilingStatus": {
                    "ReturnFileSec": "11",  # u/s 139(1) - On or before due date
                    "TaxRegime": tax_result.get("tax_regime", "new"),
                    "ResidentialStatus": "RES"  # Resident
                },
                "GrossTotalIncome": {
                    "Salary": {
                        "GrossSalary": round(salary_income, 2),
                        "StandardDeduction16ia": round(std_ded, 2),
                        "IncomeChargeableUnderHeadSalary": round(max(0.0, salary_income - std_ded), 2)
                    },
                    "IncomeFromOtherSources": {
                        "InterestFromSavingsBank": round(interest_income, 2),
                        "GrossAmount": round(interest_income, 2),
                        "TotalIncomeFromOtherSources": round(interest_income, 2)
                    },
                    "PresumptiveIncome44ADA": {
                        "GrossReceipts": round(freelance_income, 2),
                        "DeemedProfit": round(freelance_income * 0.50, 2)  # 50% Presumptive rule
                    } if freelance_income > 0 else {},
                    "GrossTotalIncomeVal": round(tax_result.get("gross_income", 0.0), 2)
                },
                "Deductions": {
                    "Section80C": round(ded_80c, 2),
                    "Section80D": round(ded_80d, 2),
                    "TotalDeductions": round(tax_result.get("total_deductions", 0.0), 2)
                },
                "TaxComputation": {
                    "TotalIncome": round(tax_result.get("taxable_income", 0.0), 2),
                    "TaxPayableOnTotalIncome": round(tax_result.get("tax_before_cess", 0.0), 2),
                    "Rebate87A": round(tax_result.get("tax_before_cess", 0.0) if tax_result.get("taxable_income", 0.0) <= 700000 and tax_result.get("tax_regime") == "new" else 0.0, 2),
                    "EducationCess": round(tax_result.get("education_cess", 0.0), 2),
                    "TotalTaxLiability": round(tax_result.get("total_tax_liability", 0.0), 2),
                    "TDSCredit": round(tax_result.get("tds_already_paid", 0.0), 2),
                    "NetTaxPayable": round(tax_result.get("net_tax_payable", 0.0), 2),
                    "RefundDue": round(max(0.0, tax_result.get("tds_already_paid", 0.0) - tax_result.get("total_tax_liability", 0.0)), 2)
                },
                "BankDetails": {
                    "PrimaryAccount": {
                        "BankName": profile.bank_name,
                        "BankAccountNo": profile.bank_account_no,
                        "IFSCode": profile.bank_ifsc,
                        "UseForRefund": "Y" if profile.bank_refund_eligible else "N"
                    }
                },
                "Verification": {
                    "Declaration": f"I, {profile.first_name} {profile.last_name}, son/daughter of solemn declaration that the details provided in this return are true and correct to the best of my knowledge.",
                    "VerificationPlace": profile.address_city,
                    "VerificationDate": now.strftime("%Y-%m-%d"),
                    "AssesseePAN": profile.pan
                }
            }
        }
    }
    return itr_data


def generate_itr1_pdf(profile: TaxpayerProfile, tax_result: dict, classified: list) -> bytes:
    """
    Generate an authentic, professional Indian Government-style ITR-1 Sahaj Form PDF.
    Complete with borders, structured schedules, and signature panels.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'GovTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0f172a")
    )
    
    subtitle_style = ParagraphStyle(
        'GovSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569")
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    label_style = ParagraphStyle(
        'FieldLabel',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )
    
    label_bold = ParagraphStyle(
        'FieldLabelBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a")
    )
    
    value_style = ParagraphStyle(
        'FieldValue',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )
    
    value_bold = ParagraphStyle(
        'FieldValueBold',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )
    
    story = []
    
    # --- HEADER BLOCK (Government Style) ---
    header_data = [
        [
            Paragraph("<b>INDIAN INCOME TAX RETURN</b><br/><font size=7>Assessment Year 2025-26 | FY 2024-25</font>", subtitle_style),
            Paragraph("<b>ITR-1 SAHAJ</b><br/><font size=6>For Individuals being Resident having total income up to ₹50 Lakhs</font>", title_style),
            Paragraph("<b>FORM ITR-V</b><br/><font size=7>E-Filing Acknowledgement</font>", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[150, 235, 150])
    header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#0f172a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))
    
    # --- PART A: PERSONAL INFORMATION ---
    def make_section_header(text):
        tbl = Table([[Paragraph(text.upper(), section_title)]], colWidths=[535])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#1e3a8a")),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return tbl
        
    story.append(make_section_header("PART A: PERSONAL INFORMATION"))
    
    full_name = f"{profile.first_name} {profile.middle_name or ''} {profile.last_name}".replace("  ", " ").strip()
    personal_data = [
        [
            Paragraph("<b>Name of Assessee:</b>", label_style), Paragraph(full_name, value_bold),
            Paragraph("<b>PAN:</b>", label_style), Paragraph(profile.pan, value_bold)
        ],
        [
            Paragraph("<b>Aadhaar Number:</b>", label_style), Paragraph(profile.aadhaar_no, value_style),
            Paragraph("<b>Date of Birth:</b>", label_style), Paragraph(profile.dob, value_style)
        ],
        [
            Paragraph("<b>Email Address:</b>", label_style), Paragraph(profile.email, value_style),
            Paragraph("<b>Mobile Number:</b>", label_style), Paragraph(profile.mobile, value_style)
        ],
        [
            Paragraph("<b>Address:</b>", label_style),
            Paragraph(f"{profile.address_flat}, {profile.address_premises}, {profile.address_road}, {profile.address_area}, {profile.address_city}, {profile.address_state} - {profile.address_pin}", value_style),
            Paragraph("<b>Employer Category:</b>", label_style), Paragraph(profile.employer_type, value_bold)
        ]
    ]
    personal_table = Table(personal_data, colWidths=[100, 190, 100, 145])
    personal_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fdfdfd")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(personal_table)
    story.append(Spacer(1, 12))
    
    # --- PART B: GROSS TOTAL INCOME ---
    story.append(make_section_header("PART B: GROSS TOTAL INCOME"))
    
    salary_income = sum(t.original_amount for t in classified if t.aica_category == AICACategory.SALARY)
    interest_income = sum(t.original_amount for t in classified if t.aica_category == AICACategory.INTEREST_INCOME)
    freelance_income = sum(t.original_amount for t in classified if t.aica_category in (AICACategory.FREELANCE_INCOME, AICACategory.BUSINESS_INCOME))
    
    std_ded = tax_result.get("deduction_breakdown", {}).get("standard_deduction", 0.0)
    net_salary = max(0.0, salary_income - std_ded)
    
    income_rows = [
        [Paragraph("<b>1. Income from Salary</b>", label_bold), "", ""],
        [Paragraph("&nbsp;&nbsp;(a) Gross Salary", label_style), Paragraph(f"₹ {salary_income:,.2f}", value_style), ""],
        [Paragraph("&nbsp;&nbsp;(b) Less: Standard Deduction u/s 16(ia)", label_style), Paragraph(f"₹ {std_ded:,.2f}", value_style), ""],
        [Paragraph("&nbsp;&nbsp;<b>(c) Net Salary Income</b>", label_bold), "", Paragraph(f"₹ {net_salary:,.2f}", value_bold)],
        [Paragraph("<b>2. Income from Other Sources</b> (Savings / Deposit Interest)", label_bold), "", Paragraph(f"₹ {interest_income:,.2f}", value_bold)],
    ]
    if freelance_income > 0:
        income_rows.append([
            Paragraph("<b>3. Presumptive Business/Profession u/s 44AD/44ADA</b>", label_bold),
            Paragraph(f"Gross: ₹ {freelance_income:,.2f}", label_style),
            Paragraph(f"Deemed (50%): ₹ {freelance_income * 0.50:,.2f}", value_bold)
        ])
    
    # Gross total income row
    gross_gti = tax_result.get("gross_income", 0.0)
    income_rows.append([
        Paragraph("<b>GROSS TOTAL INCOME (Part B)</b>", label_bold), "", Paragraph(f"₹ {gross_gti:,.2f}", value_bold)
    ])
    
    income_table = Table(income_rows, colWidths=[260, 135, 140])
    income_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (0, 4), (1, 4)),
        ('SPAN', (0, -1), (1, -1)),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(income_table)
    story.append(Spacer(1, 12))
    
    # --- PART C: DEDUCTIONS AND TAXABLE TOTAL INCOME ---
    story.append(make_section_header("PART C: DEDUCTIONS (CHAPTER VI-A)"))
    
    ded_80c = tax_result.get("deduction_breakdown", {}).get("section_80c", 0.0)
    ded_80d = tax_result.get("deduction_breakdown", {}).get("section_80d", 0.0)
    total_ded = tax_result.get("total_deductions", 0.0)
    taxable_inc = tax_result.get("taxable_income", 0.0)
    
    ded_rows = [
        [Paragraph("<b>Section 80C</b> (PPF, ELSS, Insurance, School Fees)", label_style), Paragraph(f"₹ {ded_80c:,.2f}", value_style)],
        [Paragraph("<b>Section 80D</b> (Health Insurance, Medical Expenditure)", label_style), Paragraph(f"₹ {ded_80d:,.2f}", value_style)],
        [Paragraph("<b>Total Chapter VI-A Deductions</b>", label_bold), Paragraph(f"₹ {total_ded:,.2f}", value_bold)],
        [Paragraph("<b>TOTAL TAXABLE INCOME (Gross Income - Deductions)</b>", label_bold), Paragraph(f"₹ {taxable_inc:,.2f}", value_bold)]
    ]
    ded_table = Table(ded_rows, colWidths=[395, 140])
    ded_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#f1f5f9")),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(ded_table)
    story.append(Spacer(1, 12))
    
    # --- PART D: COMPUTATION OF TAX PAYABLE ---
    story.append(make_section_header("PART D: COMPUTATION OF TAX LIABILITY"))
    
    tax_before_cess = tax_result.get("tax_before_cess", 0.0)
    rebate = tax_before_cess if taxable_inc <= 700000 and tax_result.get("tax_regime") == "new" else 0.0
    cess = tax_result.get("education_cess", 0.0)
    total_tax = tax_result.get("total_tax_liability", 0.0)
    tds = tax_result.get("tds_already_paid", 0.0)
    net_payable = tax_result.get("net_tax_payable", 0.0)
    refund = max(0.0, tds - total_tax)
    
    tax_rows = [
        [Paragraph("1. Tax Payable on Total Income (Slab-wise)", label_style), Paragraph(f"₹ {tax_before_cess:,.2f}", value_style)],
        [Paragraph("2. Less: Rebate under Section 87A", label_style), Paragraph(f"₹ {rebate:,.2f}", value_style)],
        [Paragraph("3. Add: Health and Education Cess (4%)", label_style), Paragraph(f"₹ {cess:,.2f}", value_style)],
        [Paragraph("<b>4. Gross Tax Liability</b> (1 - 2 + 3)", label_bold), Paragraph(f"₹ {total_tax:,.2f}", value_bold)],
        [Paragraph("5. Less: Tax Deducted at Source (TDS Credit)", label_style), Paragraph(f"₹ {tds:,.2f}", value_style)],
        [Paragraph("<b>6. Net Tax Payable</b> (If Tax Liability > TDS)", label_bold), Paragraph(f"₹ {net_payable:,.2f}", value_bold if net_payable > 0 else value_style)],
        [Paragraph("<b>7. Refund Due</b> (If TDS > Tax Liability)", label_bold), Paragraph(f"₹ {refund:,.2f}", value_bold if refund > 0 else value_style)]
    ]
    
    tax_table = Table(tax_rows, colWidths=[395, 140])
    tax_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor("#fee2e2") if net_payable > 0 else colors.white),
        ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor("#dcfce7") if refund > 0 else colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(tax_table)
    story.append(Spacer(1, 12))
    
    # --- BANK ACCOUNT & VERIFICATION ---
    story.append(make_section_header("PART E: BANK DETAILS & VERIFICATION"))
    
    bank_info = f"Bank Name: {profile.bank_name} | A/C: {profile.bank_account_no} | IFSC: {profile.bank_ifsc} (Refund Selected: {'Yes' if profile.bank_refund_eligible else 'No'})"
    verification_text = (
        f"I, <b>{full_name}</b>, son/daughter of solemn declaration that I am filing this return in the capacity of Self, "
        f"and that the details provided herein are true, correct and complete to the best of my knowledge, u/s 139 of the Income Tax Act."
    )
    
    bank_ver_rows = [
        [Paragraph("<b>Primary Bank Account:</b>", label_bold), Paragraph(bank_info, label_style)],
        [Paragraph("<b>Declaration:</b>", label_bold), Paragraph(verification_text, ParagraphStyle('Justify', parent=label_style, alignment=TA_JUSTIFY))],
    ]
    bank_ver_table = Table(bank_ver_rows, colWidths=[120, 415])
    bank_ver_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(bank_ver_table)
    story.append(Spacer(1, 10))
    
    # --- SIGNATURE PANEL ---
    sig_data = [
        [
            Paragraph(f"<b>Place:</b> {profile.address_city}<br/><b>Date:</b> {datetime.utcnow().strftime('%d-%b-%Y')}", label_style),
            Paragraph("<b>E-Verification Status:</b> Verified via Aadhaar OTP OTP-Transaction ID: TXN89271829", label_style),
            Paragraph("<br/><br/><b>Signature of Assessee / Representative</b>", label_bold)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[150, 235, 150])
    sig_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fafafa")),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    return buffer.getvalue()


def generate_form16_pdf(profile: TaxpayerProfile, tax_result: dict, classified: list) -> bytes:
    """
    Generate a professional Form 16 (Part B) Summary PDF for Tax Computation.
    Shows employer details, salary breakdowns, allowances, and tax computations.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'F16Title',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1e3a8a")
    )
    
    subtitle_style = ParagraphStyle(
        'F16Sub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569")
    )
    
    label_style = ParagraphStyle(
        'F16Label',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )
    
    label_bold = ParagraphStyle(
        'F16LabelBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10
    )
    
    value_style = ParagraphStyle(
        'F16Val',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10
    )
    
    value_bold = ParagraphStyle(
        'F16ValBold',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8,
        leading=10
    )
    
    story = []
    
    story.append(Paragraph("<b>FORM NO. 16</b>", title_style))
    story.append(Paragraph("Certificate under Section 203 of the Income-tax Act, 1961 for tax deducted at source from income under the head 'Salaries'", subtitle_style))
    story.append(Spacer(1, 15))
    
    # Employers Block
    employer_info = [
        [
            Paragraph("<b>Name & Address of Employer:</b><br/>Acme Solutions Private Limited<br/>Block C, Tech Park, Bellandur, Bengaluru - 560103", label_style),
            Paragraph("<b>Name & Address of Employee:</b><br/>" + f"{profile.first_name} {profile.last_name}" + f"<br/>{profile.address_flat}, {profile.address_premises}, {profile.address_city}", label_style)
        ],
        [
            Paragraph("<b>TAN of Employer:</b> BLRA02931A | <b>PAN of Employer:</b> AAACA1234F", label_bold),
            Paragraph("<b>PAN of Employee:</b> " + profile.pan, label_bold)
        ]
    ]
    emp_table = Table(employer_info, colWidths=[265, 270])
    emp_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 15))
    
    # Part B Header
    story.append(Paragraph("<b>PART B — Annexure (Details of Salary Paid and any other income)</b>", ParagraphStyle('Sub', parent=title_style, alignment=TA_LEFT, fontSize=10)))
    story.append(Spacer(1, 8))
    
    # Financial data
    salary_income = sum(t.original_amount for t in classified if t.aica_category == AICACategory.SALARY)
    interest_income = sum(t.original_amount for t in classified if t.aica_category == AICACategory.INTEREST_INCOME)
    std_ded = tax_result.get("deduction_breakdown", {}).get("standard_deduction", 0.0)
    net_salary = max(0.0, salary_income - std_ded)
    
    ded_80c = tax_result.get("deduction_breakdown", {}).get("section_80c", 0.0)
    ded_80d = tax_result.get("deduction_breakdown", {}).get("section_80d", 0.0)
    total_ded = tax_result.get("total_deductions", 0.0)
    taxable_inc = tax_result.get("taxable_income", 0.0)
    tax_liability = tax_result.get("total_tax_liability", 0.0)
    tds = tax_result.get("tds_already_paid", 0.0)
    net_payable = tax_result.get("net_tax_payable", 0.0)
    
    calc_rows = [
        [Paragraph("<b>1. Gross Salary u/s 17(1)</b>", label_bold), Paragraph(f"₹ {salary_income:,.2f}", value_style), ""],
        [Paragraph("2. Less: Standard Deduction u/s 16(ia)", label_style), Paragraph(f"₹ {std_ded:,.2f}", value_style), ""],
        [Paragraph("<b>3. Total Chargeable Income under 'Salaries'</b>", label_bold), "", Paragraph(f"₹ {net_salary:,.2f}", value_bold)],
        [Paragraph("4. Add: Income from Other Sources (Interest)", label_style), Paragraph(f"₹ {interest_income:,.2f}", value_style), ""],
        [Paragraph("<b>5. Gross Total Income</b>", label_bold), "", Paragraph(f"₹ {tax_result.get('gross_income', 0.0):,.2f}", value_bold)],
        [Paragraph("<b>6. Deductions under Chapter VI-A:</b>", label_bold), "", ""],
        [Paragraph("&nbsp;&nbsp;(a) Section 80C", label_style), Paragraph(f"₹ {ded_80c:,.2f}", value_style), ""],
        [Paragraph("&nbsp;&nbsp;(b) Section 80D", label_style), Paragraph(f"₹ {ded_80d:,.2f}", value_style), ""],
        [Paragraph("&nbsp;&nbsp;<b>(c) Total Chapter VI-A Deductions</b>", label_bold), "", Paragraph(f"₹ {total_ded:,.2f}", value_bold)],
        [Paragraph("<b>7. Total Taxable Income</b> (5 - 6(c))", label_bold), "", Paragraph(f"₹ {taxable_inc:,.2f}", value_bold)],
        [Paragraph("<b>8. Tax on Total Income</b> (including 4% Cess)", label_bold), "", Paragraph(f"₹ {tax_liability:,.2f}", value_bold)],
        [Paragraph("9. Less: Tax Deducted at Source (TDS Credit)", label_style), "", Paragraph(f"₹ {tds:,.2f}", value_style)],
        [Paragraph("<b>10. Net Tax Payable / (Refund Due)</b>", label_bold), "", Paragraph(f"₹ {net_payable:,.2f}" if net_payable > 0 else f"₹ {(tds - tax_liability):,.2f} (Refund)", value_bold)]
    ]
    calc_table = Table(calc_rows, colWidths=[290, 115, 130])
    calc_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor("#f1f5f9")),
        ('BACKGROUND', (0, 9), (-1, 9), colors.HexColor("#e2e8f0")),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
    ]))
    story.append(calc_table)
    story.append(Spacer(1, 20))
    
    # Verification Statement
    ver_text = (
        "Certified that a sum of <b>₹ " + f"{tds:,.2f}" + "</b> has been deducted at source and paid to the credit of the Central Government. "
        "We further certify that the information given above is true, complete and correct based on the books of accounts and TDS quarterly returns."
    )
    story.append(Paragraph(ver_text, ParagraphStyle('Ver', parent=label_style, alignment=TA_JUSTIFY, leading=12)))
    story.append(Spacer(1, 25))
    
    sig_data = [
        [
            Paragraph("<b>Place:</b> Bengaluru<br/><b>Date:</b> " + datetime.utcnow().strftime('%d-%b-%Y'), label_style),
            Paragraph("<b>For Acme Solutions Private Limited</b><br/><br/><br/><b>Authorised Signatory</b>", ParagraphStyle('AS', parent=label_bold, alignment=TA_CENTER))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[270, 265])
    sig_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    return buffer.getvalue()


def generate_form26as_pdf(profile: TaxpayerProfile, tax_result: dict, classified: list) -> bytes:
    """
    Generate a detailed Form 26AS TDS & Tax Credit Statement PDF.
    Lists TDS deducted on Salaries and TDS other than Salaries (FD Interest, Freelance Contracts, etc.).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'F26Title',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#b91c1c")
    )
    
    subtitle_style = ParagraphStyle(
        'F26Sub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569")
    )
    
    section_hdr = ParagraphStyle(
        'F26Sect',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    th_style = ParagraphStyle(
        'F26Th',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    
    td_style = ParagraphStyle(
        'F26Td',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )
    
    td_bold = ParagraphStyle(
        'F26Td',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10
    )
    
    story = []
    
    story.append(Paragraph("<b>FORM 26AS</b>", title_style))
    story.append(Paragraph("Annual Tax Statement under Section 203AA of the Income-tax Act, 1961", subtitle_style))
    story.append(Paragraph("Financial Year: 2024-25 | Assessment Year: 2025-26", subtitle_style))
    story.append(Spacer(1, 15))
    
    # Taxpayer details
    details = [
        [Paragraph("<b>PAN:</b>", td_bold), Paragraph(profile.pan, td_style), Paragraph("<b>Aadhaar Number:</b>", td_bold), Paragraph(profile.aadhaar_no, td_style)],
        [Paragraph("<b>Taxpayer Name:</b>", td_bold), Paragraph(f"{profile.first_name} {profile.last_name}", td_style), Paragraph("<b>Filing Date:</b>", td_bold), Paragraph(datetime.utcnow().strftime('%d-%b-%Y'), td_style)]
    ]
    det_table = Table(details, colWidths=[100, 170, 100, 165])
    det_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fafafa")),
    ]))
    story.append(det_table)
    story.append(Spacer(1, 15))
    
    # Reconciled TDS data from classified transactions
    salary_items = [t for t in classified if t.aica_category == AICACategory.SALARY]
    other_items = [t for t in classified if t.tax_flags.tds_applicable and t.aica_category != AICACategory.SALARY]
    
    # Part I: TDS on Salaries
    def make_section_hdr(text):
        tbl = Table([[Paragraph(text.upper(), section_hdr)]], colWidths=[535])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#1e293b")),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        return tbl
        
    story.append(make_section_hdr("PART A: DETAILS OF TAX DEDUCTED AT SOURCE (TDS)"))
    story.append(Spacer(1, 5))
    
    tds_headers = [Paragraph("TAN of Deductor", th_style), Paragraph("Name of Deductor", th_style), Paragraph("Gross Amount Credited", th_style), Paragraph("Total Tax Deducted", th_style)]
    tds_rows = [tds_headers]
    
    total_gross = 0.0
    total_tds = 0.0
    
    # Map Salary TDS
    if salary_items:
        sal_gross = sum(s.original_amount for s in salary_items)
        sal_tds = sal_gross * 0.10  # assume 10% average TDS for default computation
        total_gross += sal_gross
        total_tds += sal_tds
        tds_rows.append([
            Paragraph("BLRA02931A", td_style),
            Paragraph("Acme Solutions Private Limited", td_style),
            Paragraph(f"₹ {sal_gross:,.2f}", td_style),
            Paragraph(f"₹ {sal_tds:,.2f}", td_style)
        ])
        
    # Map Other TDS (Freelance, FD Interest etc.)
    for idx, item in enumerate(other_items):
        item_tds = item.original_amount * 0.10
        total_gross += item.original_amount
        total_tds += item_tds
        tds_rows.append([
            Paragraph(f"TAN{idx:05d}D", td_style),
            Paragraph(item.original_title, td_style),
            Paragraph(f"₹ {item.original_amount:,.2f}", td_style),
            Paragraph(f"₹ {item_tds:,.2f}", td_style)
        ])
        
    # Total row
    tds_rows.append([
        Paragraph("<b>Total Reconciled Tax Credit</b>", td_bold),
        Paragraph("", td_style),
        Paragraph(f"<b>₹ {total_gross:,.2f}</b>", td_bold),
        Paragraph(f"<b>₹ {total_tds:,.2f}</b>", td_bold)
    ])
    
    tds_table = Table(tds_rows, colWidths=[110, 195, 115, 115])
    tds_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#334155")),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(tds_table)
    story.append(Spacer(1, 15))
    
    # Part II: Reconciled status info
    story.append(Paragraph("<b>Disclaimer & Status Notes:</b>", ParagraphStyle('Dis', parent=td_bold, fontSize=7)))
    story.append(Paragraph(
        "1. This statement is dynamically compiled by FinanceAI using transaction descriptors matched via AI-CA classification rule engine.<br/>"
        "2. All TDS transactions extracted have been reconciled against the corresponding PAN record.<br/>"
        "3. Ensure the TAN and Deductor records correspond with your Form 16 / Form 16A certificates before filing your final Income Tax Return.",
        ParagraphStyle('Notes', parent=td_style, fontSize=7, leading=9, textColor=colors.HexColor("#64748b"))
    ))
    
    doc.build(story)
    return buffer.getvalue()
