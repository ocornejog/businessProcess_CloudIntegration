# test_eligibility.py
from decimal import Decimal
from services.models import LoanApplication, LoanStatus
from services.eligibility import evaluate_eligibility
from services.config import LOAN_RULES

def print_evaluation_results(scenario_name, result):
    """Helper function to print evaluation results in a clear format"""
    print(f"\n=== {scenario_name} ===")
    print(f"Eligibility Result: {'APPROVED' if result['is_eligible'] else 'REJECTED'}")
    print(f"Credit Score: {result['credit_score']} (Minimum required: {LOAN_RULES['MIN_CREDIT_SCORE']})")
    print(f"DTI Ratio: {result['dti_ratio']:.2%} (Maximum allowed: {LOAN_RULES['MAX_DTI_RATIO']:.2%})")
    print(f"Income Multiplier: {result['income_multiplier']:.2f}x (Maximum allowed: {LOAN_RULES['MIN_INCOME_MULTIPLIER']}x)")
    print("\nDetailed Evaluation:")
    for criterion, meets_requirement in result['evaluation_details'].items():
        print(f"✓ {criterion}: {'PASS' if meets_requirement else 'FAIL'}")
    print(f"Final Status: {result['status']}")
    print("="* 50)

def test_strong_application():
    """Test a financially strong application that should be clearly eligible"""
    strong_application = {
        'application_id': 'TEST_STRONG_001',
        'client_name': 'Alexandre Dubois',  # High credit score simulation
        'loan_amount': 2500000,
        'loan_duration_years': 25,
        'monthly_income': 35000,  # €420,000 annual income
        'monthly_expenses': 8000   # DTI ratio: 0.229
    }
    
    result = evaluate_eligibility.apply(args=[strong_application]).get()
    print_evaluation_results("Strong Application Test", result)

def test_borderline_application():
    """Test an application that's just within acceptable limits"""
    borderline_application = {
        'application_id': 'TEST_BORDERLINE_001',
        'client_name': 'Jean Martin',  # Different name to simulate different credit score
        'loan_amount': 1200000,
        'loan_duration_years': 30,  # Maximum allowed duration
        'monthly_income': 25000,    # €300,000 annual income
        'monthly_expenses': 10000   # DTI ratio: 0.4 (close to limit)
    }
    
    result = evaluate_eligibility.apply(args=[borderline_application]).get()
    print_evaluation_results("Borderline Application Test", result)

def test_weak_application():
    """Test an application that should be clearly ineligible"""
    weak_application = {
        'application_id': 'TEST_WEAK_001',
        'client_name': 'Pierre Durand',
        'loan_amount': 3000000,
        'loan_duration_years': 35,  # Exceeds maximum duration
        'monthly_income': 15000,    # €180,000 annual income - too low for loan amount
        'monthly_expenses': 8000    # DTI ratio: 0.533 - exceeds maximum
    }
    
    result = evaluate_eligibility.apply(args=[weak_application]).get()
    print_evaluation_results("Weak Application Test", result)

def test_high_dti_application():
    """Test an application with good income but high debt-to-income ratio"""
    high_dti_application = {
        'application_id': 'TEST_DTI_001',
        'client_name': 'Sophie Lefevre',
        'loan_amount': 1500000,
        'loan_duration_years': 20,
        'monthly_income': 30000,     # €360,000 annual income
        'monthly_expenses': 15000    # DTI ratio: 0.5 - exceeds maximum
    }
    
    result = evaluate_eligibility.apply(args=[high_dti_application]).get()
    print_evaluation_results("High DTI Application Test", result)

def test_income_multiplier_violation():
    """Test an application where loan amount is too high relative to income"""
    income_violation_application = {
        'application_id': 'TEST_INCOME_001',
        'client_name': 'Marie Lambert',
        'loan_amount': 2000000,
        'loan_duration_years': 25,
        'monthly_income': 20000,    # €240,000 annual income - loan is 8.33x income
        'monthly_expenses': 6000    # DTI ratio: 0.3 - acceptable
    }
    
    result = evaluate_eligibility.apply(args=[income_violation_application]).get()
    print_evaluation_results("Income Multiplier Violation Test", result)

if __name__ == "__main__":
    print("Starting eligibility service tests...")
    
    # Run all tests
    test_strong_application()
    test_borderline_application()
    test_weak_application()
    test_high_dti_application()
    test_income_multiplier_violation()
    
    print("\nEligibility service tests completed.")