import asyncio
import json
from decimal import Decimal
from main import LoanApplicationProcessor
from services.models import LoanApplication

async def test_reimbursement_rules():
    """
    Test cases for reimbursement agreement verification and eligibility
    Tests various scenarios where loans should fail reimbursement rules or eligibility
    """
    # Test cases with their expected results
    test_cases = [
        {
            "name": "Excessive Monthly Payment",
            "application": LoanApplication(
                client_name="Test User 1",
                address="123 Test St",
                email="test1@example.com",
                phone="+1234567890",
                loan_amount=Decimal("1500000.00"),  # High loan amount to generate high monthly payment
                loan_duration_years=15,             # Shorter duration to increase monthly payments
                property_description="Test Property 1",
                monthly_income=Decimal("20000.00"),
                monthly_expenses=Decimal("5000.00")
            ),
            "expected_status": "REJECTED",
            "expected_reason": "Monthly payment exceeds maximum allowed"
        },
        {
            "name": "Excessive Duration",
            "application": LoanApplication(
                client_name="Test User 2",
                address="456 Test Ave",
                email="test2@example.com",
                phone="+1234567891",
                loan_amount=Decimal("300000.00"),
                loan_duration_years=35,             # Exceeds max_duration_years (30)
                property_description="Test Property 2",
                monthly_income=Decimal("8000.00"),
                monthly_expenses=Decimal("2000.00")
            ),
            "expected_status": "REJECTED",
            "expected_reason": "Loan duration exceeds maximum allowed"
        },
        {
            "name": "High Repayment Ratio",
            "application": LoanApplication(
                client_name="Test User 3",
                address="789 Test Blvd",
                email="test3@example.com",
                phone="+1234567892",
                loan_amount=Decimal("500000.00"),
                loan_duration_years=30,
                property_description="Test Property 3",
                monthly_income=Decimal("6000.00"),
                monthly_expenses=Decimal("1500.00")
            ),
            "expected_status": "REJECTED",
            "expected_reason": "Total repayment exceeds maximum allowed ratio"
        },
        {
            "name": "Ineligible Due to High DTI",
            "application": LoanApplication(
                client_name="Test User 4",
                address="101 Test Lane",
                email="test4@example.com",
                phone="+1234567893",
                loan_amount=Decimal("400000.00"),
                loan_duration_years=25,
                property_description="Test Property 4",
                monthly_income=Decimal("5000.00"),
                monthly_expenses=Decimal("4000.00"),  # Very high expenses relative to income
            ),
            "expected_status": "REJECTED_INELIGIBLE",
            "expected_reason": "Debt-to-Income ratio too high"
        }
    ]

    # Load reimbursement rules for verification
    with open('reimbursement_rules.json', 'r') as f:
        rules = json.load(f)

    print("\nStarting Loan Application Test Cases")
    print("=" * 50)

    for test_case in test_cases:
        print(f"\nTest Case: {test_case['name']}")
        print("-" * 30)

        # Process the loan application
        processor = LoanApplicationProcessor()
        result = await processor.process_loan_application(test_case['application'])

        # Verify results
        print(f"Application Status: {result['final_status']}")
        
        # Check if the result matches expected outcome
        if result['final_status'] == test_case['expected_status']:
            print("✅ Test PASSED")
            print(f"Expected reason: {test_case['expected_reason']}")
            print(f"Actual result details: {result.get('notification', '')}")
        else:
            print("❌ Test FAILED")
            print(f"Expected status: {test_case['expected_status']}")
            print(f"Actual status: {result['final_status']}")

        # Print relevant values for debugging
        print("\nDebug Information:")
        print(f"Loan Amount: €{test_case['application'].loan_amount:,.2f}")
        print(f"Duration: {test_case['application'].loan_duration_years} years")
        print(f"Monthly Income: €{test_case['application'].monthly_income:,.2f}")
        print(f"Monthly Expenses: €{test_case['application'].monthly_expenses:,.2f}")
        print(f"DTI Ratio: {(test_case['application'].monthly_expenses / test_case['application'].monthly_income):.2%}")
        
        # Print applicable rule limits
        print("\nApplicable Rules:")
        if test_case['expected_status'] == "REJECTED_INELIGIBLE":
            print("Eligibility Rules:")
            print(f"Max DTI Ratio: 43%")
        else:
            print("Reimbursement Rules:")
            print(f"Max Monthly Payment: €{rules['max_monthly_payment']:,.2f}")
            print(f"Max Duration: {rules['max_duration_years']} years")
            print(f"Max Repayment Ratio: {rules['max_repayment_ratio']}")

        print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(test_reimbursement_rules()) 