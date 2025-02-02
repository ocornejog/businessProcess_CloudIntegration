# main.py
import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Tuple
from pathlib import Path
import concurrent.futures

from services.models import LoanApplication, LoanStatus
from services.completeness import verify_completion
from services.eligibility import evaluate_eligibility
from services.reimbursement import prepare_reimbursement_agreement
from process_logger import ProcessLogger

class LoanApplicationProcessor:
    """
    Main processor class that implements the exact flow of the BPMN diagram:
    1. Completeness verification loop
    2. Parallel eligibility checks (credit history and property evaluation)
    3. Reimbursement agreement handling
    """
    def __init__(self):
        self.application = None
        self.current_status = None
        self.process_logger = ProcessLogger(base_dir="loan_process_logs")
        self.verification_attempts = 0
        self.MAX_VERIFICATION_ATTEMPTS = 3

    async def _verify_completeness(self, loan_application: LoanApplication) -> dict:
        """
        Calls the verify_completion task to check the completeness of the loan application.
        """
        loan_data = {
            'application_id': loan_application.application_id,
            'client_name': loan_application.client_name,
            'address': loan_application.address,
            'email': loan_application.email,
            'phone': loan_application.phone,
            'loan_amount': loan_application.loan_amount,
            'loan_duration_years': loan_application.loan_duration_years,
            'property_description': loan_application.property_description,
            'monthly_income': loan_application.monthly_income,
            'monthly_expenses': loan_application.monthly_expenses
        }
        # Convert Decimal to str for logging
        loan_data_str = {k: str(v) if isinstance(v, Decimal) else v for k, v in loan_data.items()}
        self.process_logger.log_step("Calling verify_completion with loan_data", loan_data_str)
        result = verify_completion.apply(args=[loan_data])
        try:
            response = result.get()
            # Convert Decimal to str for logging
            response_str = {k: str(v) if isinstance(v, Decimal) else v for k, v in response.items()}
            self.process_logger.log_step("Received response from verify_completion", response_str)
            return response
        except Exception as e:
            self.process_logger.log_step("Error in verify_completion", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            raise

    async def process_loan_application(self, loan_application: LoanApplication) -> Dict[str, Any]:
        """
        Main processing method following BPMN diagram flow exactly.
        """
        self.application = loan_application
        
        # Log process initiation
        self.process_logger.log_step(
            "Loan Application Process Initiated",
            {
                "application_id": loan_application.application_id,
                "client_name": loan_application.client_name,
                "loan_amount": str(loan_application.loan_amount),
                "initial_timestamp": datetime.now().isoformat()
            }
        )

        try:
            # Phase 1: Completeness Verification Loop (as per BPMN)
            is_complete = await self._execute_completeness_loop()
            if not is_complete:
                return self._finalize_process("REJECTED_INCOMPLETE")

            # Phase 2: Parallel Eligibility Evaluation (as per BPMN)
            eligibility_result = await self._parallel_eligibility_evaluation()
            if not eligibility_result['is_eligible']:
                return self._finalize_process("REJECTED_INELIGIBLE")

            # Phase 3: Reimbursement Agreement (as per BPMN)
            agreement_result = await self._handle_reimbursement_process()
            
            return self._finalize_process(agreement_result['status'])

        except Exception as e:
            self.process_logger.log_step("Process Error", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            return self._finalize_process("ERROR")

    async def _execute_completeness_loop(self) -> bool:
        """
        Implements the completeness verification loop from BPMN diagram.
        Returns True if application is complete, False if max attempts reached.
        """
        while self.verification_attempts < self.MAX_VERIFICATION_ATTEMPTS:
            self.verification_attempts += 1
            
            self.process_logger.log_step(
                f"Completeness Verification Attempt {self.verification_attempts}"
            )

            # Verify completeness
            verification_result = await self._verify_completeness(self.application)
            # Convert Decimal to str for logging
            verification_result_str = {k: str(v) if isinstance(v, Decimal) else v for k, v in verification_result.items()}
            self.process_logger.log_step("Verification result", verification_result_str)

            if verification_result['is_complete']:
                self.process_logger.log_step("Application Verified Complete", {
                    "attempts": self.verification_attempts
                })
                return True

            # If not complete and attempts remain, request updates
            if self.verification_attempts < self.MAX_VERIFICATION_ATTEMPTS:
                await self._request_application_updates(verification_result['missing_fields'])
            else:
                self.process_logger.log_step("Max Verification Attempts Reached", {
                    "total_attempts": self.verification_attempts
                })
                return False

        return False

    async def _parallel_eligibility_evaluation(self) -> Dict[str, Any]:
        """
        Implements parallel eligibility evaluation as shown in BPMN diagram.
        Executes credit history check and property evaluation concurrently.
        """
        self.process_logger.log_step("Starting Parallel Eligibility Evaluation")

        # Create tasks for parallel execution
        tasks = [
            self._verify_credit_history(),
            self._evaluate_property()
        ]

        # Execute tasks in parallel
        results = await asyncio.gather(*tasks)
        credit_result, property_result = results

        # Combine results as per BPMN gateway
        is_eligible = all([
            credit_result['meets_requirements'],
            property_result['meets_requirements']
        ])

        evaluation_details = {
            "is_eligible": is_eligible,
            "credit_evaluation": credit_result,
            "property_evaluation": property_result
        }

        self.process_logger.log_step("Eligibility Evaluation Complete", evaluation_details)
        return evaluation_details

    async def _verify_credit_history(self) -> Dict[str, Any]:
        """
        Verifies credit history as shown in BPMN diagram.
        """
        self.process_logger.log_step("Starting Credit History Verification")
        
        loan_data = {
            'application_id': self.application.application_id,
            'client_name': self.application.client_name,
            'monthly_income': float(self.application.monthly_income),
            'monthly_expenses': float(self.application.monthly_expenses)
        }
        
        result = evaluate_eligibility.apply(args=[loan_data]).get()
        
        self.process_logger.log_step("Credit History Verification Complete", result)
        return result

    async def _evaluate_property(self) -> Dict[str, Any]:
        """
        Evaluates property as shown in BPMN diagram.
        """
        self.process_logger.log_step("Starting Property Evaluation")

        property_data = {
            'application_id': self.application.application_id,
            'property_description': self.application.property_description,
            'loan_amount': float(self.application.loan_amount)
        }

        # Log property data
        self.process_logger.log_step("Property Data", property_data)
        
        # Simulate property evaluation
        # await asyncio.sleep(3)
        
        # In real implementation, this would call a property evaluation service
        evaluation_result = {
            'meets_requirements': True,
            'property_value': float(self.application.loan_amount) * 1.2,
            'location_assessment': 'Favorable',
            'risk_assessment': 'Low'
        }
        
        self.process_logger.log_step("Property Evaluation Complete", evaluation_result)
        return evaluation_result

    async def _handle_reimbursement_process(self) -> Dict[str, Any]:
        """
        Implements the reimbursement agreement process as shown in BPMN diagram.
        """
        self.process_logger.log_step("Starting Reimbursement Agreement Process")
        
        # Prepare agreement
        agreement_result = await self._prepare_reimbursement_agreement()
        
        # Handle customer review
        if agreement_result['status'] == 'AGREEMENT_PREPARED':
            review_result = await self._process_customer_review()
            return review_result
        
        return agreement_result

    async def _prepare_reimbursement_agreement(self) -> Dict[str, Any]:
        """
        Prepares the reimbursement agreement document.
        """
        loan_data = {
            'application_id': self.application.application_id,
            'loan_amount': float(self.application.loan_amount),
            'loan_duration_years': self.application.loan_duration_years
        }
        
        result = prepare_reimbursement_agreement.apply(args=[loan_data]).get()
        self.process_logger.log_step("Reimbursement Agreement Prepared", result)
        return result

    async def _process_customer_review(self) -> Dict[str, Any]:
        """
        Handles customer review of the reimbursement agreement as per BPMN.
        """
        self.process_logger.log_step("Awaiting Customer Review")
        
        # Simulate customer review time
        await asyncio.sleep(5)
        
        # In real implementation, this would wait for customer response
        # For simulation, we'll assume acceptance
        review_result = {
            'status': 'AGREEMENT_ACCEPTED',
            'customer_response': 'Accepted',
            'response_date': datetime.now().isoformat()
        }
        
        self.process_logger.log_step("Customer Review Complete", review_result)
        return review_result

    def _finalize_process(self, final_status: str) -> Dict[str, Any]:
        """
        Finalizes the loan application process with complete summary.
        """
        process_summary = {
            "application_id": self.application.application_id,
            "final_status": final_status,
            "client_name": self.application.client_name,
            "loan_amount": str(self.application.loan_amount),
            "verification_attempts": self.verification_attempts,
            "process_completion_time": datetime.now().isoformat()
        }
        
        self.process_logger.finalize_process(final_status, process_summary)
        return process_summary

async def main():
    """
    Main execution function that demonstrates the loan application process.
    """
    # Create sample loan application
    loan_application = LoanApplication(
        client_name="Alexandre Dubois",
        address="25 Avenue Montaigne, 75008 Paris, France",
        email="alexandre.dubois@email.com",
        phone="+33 6 12 34 56 78",
        loan_amount=Decimal("2500000"),
        loan_duration_years=25,
        property_description="Appartement de luxe de 250m² avec terrasse panoramique...",
        monthly_income=Decimal("35000"),
        monthly_expenses=Decimal("8000")
    )
    
    # Initialize processor and start process
    processor = LoanApplicationProcessor()
    
    try:
        result = await processor.process_loan_application(loan_application)
        
        print("\nLoan Application Process Completed")
        print("="*50)
        print(json.dumps(result, indent=2))
        print("\nDetailed logs available in:")
        print(f"- Detailed logs: {processor.process_logger.detailed_logs_dir}")
        print(f"- JSON logs: {processor.process_logger.json_logs_dir}")
        
    except Exception as e:
        print(f"\nError during process execution: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())