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
    missing_fields = []
    for field in LOAN_RULES['REQUIRED_FIELDS']:
        if not loan_data.get(field):
            missing_fields.append(field)
    
    try:
        if 'loan_amount' in loan_data:
            Decimal(str(loan_data['loan_amount']))
        if 'monthly_income' in loan_data:
            Decimal(str(loan_data['monthly_income']))
        if 'monthly_expenses' in loan_data:
            Decimal(str(loan_data['monthly_expenses']))
    except (ValueError, TypeError, InvalidOperation):
        missing_fields.append('Invalid numeric values')

    return {
        'application_id': loan_data['application_id'],
        'is_complete': len(missing_fields) == 0,
        'missing_fields': missing_fields,
        'status': LoanStatus.COMPLETE.value if len(missing_fields) == 0 else LoanStatus.INCOMPLETE.value
    }
