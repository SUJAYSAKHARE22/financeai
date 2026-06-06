import sys
import os
from datetime import datetime

# Set Python path to current directory to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.classifier_service import classify_transactions
from services.database import db
from services.tax_engine import compute_tax
from models.aica_schemas import TaxpayerProfile, TaxRegime
from models.schemas import Transaction, TransactionType, TransactionCategory
from services.itr_generator import generate_itr_json, generate_itr1_pdf, generate_form16_pdf, generate_form26as_pdf

def test_document_generation():
    print("Testing document generation services...")
    
    # 1. Instantiate mock transactions and run classifier
    txs = [
        Transaction(id="t1", title="Monthly Salary", amount=75000, type=TransactionType.INCOME, category=TransactionCategory.INCOME, date=datetime(2024, 4, 1)),
        Transaction(id="t2", title="Freelance Project", amount=15000, type=TransactionType.INCOME, category=TransactionCategory.INCOME, date=datetime(2024, 4, 5)),
        Transaction(id="t3", title="Grocery Shopping", amount=4500, type=TransactionType.EXPENSE, category=TransactionCategory.FOOD, date=datetime(2024, 4, 3)),
        Transaction(id="t4", title="Restaurant Dinner", amount=1800, type=TransactionType.EXPENSE, category=TransactionCategory.FOOD, date=datetime(2024, 4, 7)),
        Transaction(id="t5", title="Uber Rides", amount=1200, type=TransactionType.EXPENSE, category=TransactionCategory.TRANSPORT, date=datetime(2024, 4, 4)),
        Transaction(id="t6", title="Amazon Shopping", amount=3500, type=TransactionType.EXPENSE, category=TransactionCategory.SHOPPING, date=datetime(2024, 4, 6)),
        Transaction(id="t7", title="Netflix Subscription", amount=649, type=TransactionType.EXPENSE, category=TransactionCategory.ENTERTAINMENT, date=datetime(2024, 4, 1)),
        Transaction(id="t8", title="Electricity Bill", amount=2200, type=TransactionType.EXPENSE, category=TransactionCategory.BILLS, date=datetime(2024, 4, 5)),
        Transaction(id="t9", title="Gym Membership", amount=1500, type=TransactionType.EXPENSE, category=TransactionCategory.HEALTH, date=datetime(2024, 4, 1)),
        Transaction(id="t10", title="Mutual Fund SIP", amount=10000, type=TransactionType.EXPENSE, category=TransactionCategory.INVESTMENT, date=datetime(2024, 4, 3)),
    ]
    res = classify_transactions(txs, use_ai=False)
    classified = res.classified
    print(f"Classified {len(classified)} transactions.")
    
    # 2. Run tax calculations
    tax_result = compute_tax(classified, TaxRegime.NEW, "2024-25")
    print(f"Gross Income: Rs.{tax_result.gross_income}, Net Payable: Rs.{tax_result.net_tax_payable}")
    
    # 3. Create populated test taxpayer profile
    profile = TaxpayerProfile(
        first_name="Rajesh",
        last_name="Kumar",
        pan="ABCDE1234F",
        aadhaar_no="1234 5678 9012",
        dob="1985-08-15",
        email="rajesh.kumar@gmail.com",
        mobile="9876543210",
        address_flat="Flat 402, Building A",
        address_premises="Green Glen Layout",
        address_road="Outer Ring Road",
        address_area="Bellandur",
        address_city="Bengaluru",
        address_state="Karnataka",
        address_pin="560103",
        employer_type="PRIVATE",
        bank_name="HDFC Bank",
        bank_account_no="50100412345678",
        bank_ifsc="HDFC0000184",
        bank_refund_eligible=True
    )
    
    # 4. Generate JSON
    itr_json = generate_itr_json(profile, tax_result.model_dump(), classified)
    assert "ITR" in itr_json
    assert "ITR1_Sahaj" in itr_json["ITR"]
    print("SUCCESS: ITR JSON Generation Test Passed!")
    
    # 5. Generate ITR PDF
    pdf_bytes = generate_itr1_pdf(profile, tax_result.model_dump(), classified)
    assert len(pdf_bytes) > 0
    print(f"SUCCESS: ITR PDF Generation Test Passed! Size: {len(pdf_bytes)} bytes")
    
    # 6. Generate Form 16 PDF
    f16_bytes = generate_form16_pdf(profile, tax_result.model_dump(), classified)
    assert len(f16_bytes) > 0
    print(f"SUCCESS: Form 16 PDF Generation Test Passed! Size: {len(f16_bytes)} bytes")
    
    # 7. Generate Form 26AS PDF
    f26as_bytes = generate_form26as_pdf(profile, tax_result.model_dump(), classified)
    assert len(f26as_bytes) > 0
    print(f"SUCCESS: Form 26AS PDF Generation Test Passed! Size: {len(f26as_bytes)} bytes")
    
    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_document_generation()
