from celery import chain
from .models import LoanApplication, LoanStatus
from .completeness import verify_completion
from .eligibility import evaluate_eligibility
from .reimbursement import prepare_reimbursement_agreement

class LoanProcessOrchestrator:
    @staticmethod
    def start_loan_process(loan_application: LoanApplication) -> dict:
        """Orchestrate the entire loan application process as per BPMN diagram"""
        # Convert loan application to dictionary for task processing
        loan_data = {
            'application_id': loan_application.application_id,
            'client_name': loan_application.client_name,
            'address': loan_application.address,
            'email': loan_application.email,
            'phone': loan_application.phone,
            'loan_amount': float(loan_application.loan_amount),
            'loan_duration_years': loan_application.loan_duration_years,
            'property_description': loan_application.property_description,
            'monthly_income': float(loan_application.monthly_income),
            'monthly_expenses': float(loan_application.monthly_expenses)
        }
        
        # Create processing workflow according to BPMN diagram
        workflow = chain(
            verify_completion.s(loan_data),
            evaluate_eligibility.s(),
            prepare_reimbursement_agreement.s()
        )
        
        # Start the workflow
        result = workflow.apply_async()
        
        return {
            'application_id': loan_application.application_id,
            'task_id': result.id,
            'status': LoanStatus.RECEIVED.value
        }