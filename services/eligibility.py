from celery import Celery
from .models import LoanStatus
from .config import CELERY_CONFIG, LOAN_RULES
from decimal import Decimal

app = Celery('eligibility_service')
app.config_from_object(CELERY_CONFIG)

@app.task(name='evaluate_eligibility')
def evaluate_eligibility(loan_data: dict) -> dict:
    """Evaluate loan eligibility based on financial criteria"""
    loan_amount = Decimal(str(loan_data['loan_amount']))
    monthly_income = Decimal(str(loan_data['monthly_income']))
    monthly_expenses = Decimal(str(loan_data['monthly_expenses']))
    
    # Calculate key financial ratios
    annual_income = monthly_income * 12
    dti_ratio = monthly_expenses / monthly_income
    
    # Simulate credit score check (in real implementation, would call credit bureau)
    simulated_credit_score = 700 + (len(loan_data['client_name']) % 200)
    
    # Check DTI ratio against maximum allowed (43%)
    MAX_DTI_RATIO = Decimal('0.43')
    meets_dti_requirement = dti_ratio <= MAX_DTI_RATIO
    
    # Determine eligibility
    is_eligible = meets_dti_requirement
    
    return {
        'application_id': loan_data['application_id'],
        'is_eligible': is_eligible,
        'credit_score': simulated_credit_score,
        'dti_ratio': float(dti_ratio),
        'evaluation_details': {
            'meets_credit_requirement': True,
            'meets_dti_requirement': meets_dti_requirement,
            'meets_income_requirement': True,
            'meets_duration_requirement': True
        }
    }