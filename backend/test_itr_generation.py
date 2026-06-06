import sys
import os

# Set Python path to current directory to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.classifier_service import classify_transactions
from services.database import db
from services.tax_engine import compute_tax
from models.aica_schemas import TaxpayerProfile, TaxRegime
from services.itr_generator import generate_itr_json, generate_itr1_pdf, generate_form16_pdf, generate_form26as_pdf

def test_document_generation():
    print("Testing document generation services...")
    
    # 1. Fetch transactions and run classifier
    txs = db.get_all_transactions()
    res = classify_transactions(txs, use_ai=False)
    classified = res.classified
    print(f"Classified {len(classified)} transactions.")
    
    # 2. Run tax calculations
    tax_result = compute_tax(classified, TaxRegime.NEW, "2024-25")
    print(f"Gross Income: Rs.{tax_result.gross_income}, Net Payable: Rs.{tax_result.net_tax_payable}")
    
    # 3. Create default profile
    profile = TaxpayerProfile()
    
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
