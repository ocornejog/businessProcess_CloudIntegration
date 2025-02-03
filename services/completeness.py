from celery import Celery
from .models import LoanApplication, LoanStatus
from .config import CELERY_CONFIG, LOAN_RULES
import json
from decimal import Decimal, InvalidOperation

app = Celery('completeness_service')
app.config_from_object(CELERY_CONFIG)

@app.task(name='verify_completion')
def verify_completion(loan_data: dict) -> dict:
    """
    Verify if the loan application is complete according to BPMN diagram requirements
    """
    # First ensure loan_data is not None
    if not loan_data:
        return {
            'application_id': None,
            'is_complete': False,
            'missing_fields': ['All fields missing'],
            'status': LoanStatus.INCOMPLETE.value
        }

    # Get application_id first as it's needed for the response
    application_id = loan_data.get('application_id', 'UNKNOWN')
    
    # Check all required fields
    missing_fields = []
    for field in LOAN_RULES['REQUIRED_FIELDS']:
        if field not in loan_data or not loan_data[field]:
            missing_fields.append(field)
    
    # Validate numeric fields if present
    try:
        if 'loan_amount' in loan_data and loan_data['loan_amount']:
            Decimal(str(loan_data['loan_amount']))
        if 'monthly_income' in loan_data and loan_data['monthly_income']:
            Decimal(str(loan_data['monthly_income']))
        if 'monthly_expenses' in loan_data and loan_data['monthly_expenses']:
            Decimal(str(loan_data['monthly_expenses']))
    except (ValueError, TypeError, InvalidOperation):
        missing_fields.append('Invalid numeric values')

    return {
        'application_id': application_id,
        'is_complete': len(missing_fields) == 0,
        'missing_fields': missing_fields,
        'status': LoanStatus.COMPLETE.value if len(missing_fields) == 0 else LoanStatus.INCOMPLETE.value
    }
