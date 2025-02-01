from celery import Celery
from .models import LoanStatus
from .config import CELERY_CONFIG
from datetime import datetime, timedelta
from decimal import Decimal

app = Celery('reimbursement_service')
app.config_from_object(CELERY_CONFIG)

@app.task(name='prepare_reimbursement_agreement')
def prepare_reimbursement_agreement(loan_data: dict) -> dict:
    """Prepare reimbursement agreement for approved loans"""
    loan_amount = Decimal(str(loan_data['loan_amount']))
    duration_years = int(loan_data['loan_duration_years'])
    
    # Simple interest rate calculation (in reality, would be more complex)
    base_rate = Decimal('0.03')
    risk_premium = Decimal('0.01')
    annual_rate = base_rate + risk_premium
    
    # Calculate monthly payment (simplified)
    monthly_rate = annual_rate / 12
    num_payments = duration_years * 12
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    return {
        'application_id': loan_data['application_id'],
        'agreement_details': {
            'loan_amount': float(loan_amount),
            'duration_years': duration_years,
            'annual_interest_rate': float(annual_rate),
            'monthly_payment': float(monthly_payment),
            'total_payments': num_payments,
            'first_payment_date': (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d'),
            'total_repayment': float(monthly_payment * num_payments)
        },
        'status': LoanStatus.PENDING_AGREEMENT.value
    }
