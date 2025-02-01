# test_completeness.py
from decimal import Decimal
from services.models import LoanApplication, LoanStatus
from services.completeness import verify_completion

def test_complete_application():
    """Test a complete and valid loan application"""
    complete_data = {
        'application_id': 'TEST_COMPLETE_001',
        'client_name': 'Alexandre Dubois',
        'address': '25 Avenue Montaigne, 75008 Paris, France',
        'email': 'alexandre.dubois@email.com',
        'phone': '+33 6 12 34 56 78',
        'loan_amount': 2500000,
        'loan_duration_years': 25,
        'property_description': 'Appartement de luxe de 250m² avec terrasse panoramique',
        'monthly_income': 35000,
        'monthly_expenses': 8000
    }
    
    print("\nTesting complete application:")
    result = verify_completion.apply(args=[complete_data]).get()
    print(f"Result: {result}")
    print(f"Is complete: {result['is_complete']}")
    print(f"Status: {result['status']}")
    if not result['is_complete']:
        print(f"Missing fields: {result['missing_fields']}")

def test_incomplete_application():
    """Test an incomplete loan application"""
    incomplete_data = {
        'application_id': 'TEST_INCOMPLETE_001',
        'client_name': 'Alexandre Dubois',
        'address': '25 Avenue Montaigne, 75008 Paris, France',
        # Missing email
        'phone': '+33 6 12 34 56 78',
        'loan_amount': 2500000,
        # Missing loan_duration_years
        'property_description': 'Appartement de luxe',
        'monthly_income': 35000,
        # Missing monthly_expenses
    }
    
    print("\nTesting incomplete application:")
    result = verify_completion.apply(args=[incomplete_data]).get()
    print(f"Result: {result}")
    print(f"Is complete: {result['is_complete']}")
    print(f"Status: {result['status']}")
    if not result['is_complete']:
        print(f"Missing fields: {result['missing_fields']}")

def test_invalid_numeric_values():
    """Test an application with invalid numeric values"""
    invalid_data = {
        'application_id': 'TEST_INVALID_001',
        'client_name': 'Alexandre Dubois',
        'address': '25 Avenue Montaigne, 75008 Paris, France',
        'email': 'alexandre.dubois@email.com',
        'phone': '+33 6 12 34 56 78',
        'loan_amount': 'invalid_amount',  # Invalid numeric value
        'loan_duration_years': 25,
        'property_description': 'Appartement de luxe',
        'monthly_income': 'not_a_number',  # Invalid numeric value
        'monthly_expenses': 8000
    }
    
    print("\nTesting invalid numeric values:")
    result = verify_completion.apply(args=[invalid_data]).get()
    print(f"Result: {result}")
    print(f"Is complete: {result['is_complete']}")
    print(f"Status: {result['status']}")
    if not result['is_complete']:
        print(f"Missing fields: {result['missing_fields']}")

if __name__ == "__main__":
    print("Starting completeness service tests...")
    
    # Run all tests
    test_complete_application()
    test_incomplete_application()
    test_invalid_numeric_values()
    
    print("\nCompleteness service tests completed.")