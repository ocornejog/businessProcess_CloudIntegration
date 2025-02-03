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

    async def process_loan_application(self, loan_application: LoanApplication) -> Dict[str, Any]:
        """
        Main processing method following BPMN diagram flow exactly.
        """
        self.application = loan_application
        
        # Debug logging
        print("DEBUG: Loan Application Object:")
        print(f"DEBUG: Has loan_amount attribute: {hasattr(self.application, 'loan_amount')}")
        if hasattr(self.application, 'loan_amount'):
            print(f"DEBUG: loan_amount value: {self.application.loan_amount}")
        print(f"DEBUG: Application vars: {vars(self.application)}")
        
        # Log process initiation with proper string conversion of Decimal values
        initial_log = {
            "application_id": self.application.application_id,
            "client_name": self.application.client_name,
            "initial_timestamp": datetime.now().isoformat()
        }
        
        # Only add loan_amount if it exists
        if hasattr(self.application, 'loan_amount'):
            initial_log["loan_amount"] = str(self.application.loan_amount)
            
        self.process_logger.log_step(
            "Loan Application Process Initiated",
            initial_log
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
            print(f"DEBUG: Exception occurred: {type(e).__name__}: {str(e)}")
            print(f"DEBUG: Exception location: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
            self.process_logger.log_step("Process Error", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_location": f"{e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}"
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
            verification_result = await self._verify_completeness()
            
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
        """
        self.process_logger.log_step("Starting Parallel Eligibility Evaluation")

        try:
            # Create tasks for parallel execution
            tasks = [
                self._verify_credit_history(),
                self._evaluate_property()
            ]

            # Execute tasks in parallel
            results = await asyncio.gather(*tasks)
            credit_result, property_result = results

            print("DEBUG: Credit Result:", credit_result)
            print("DEBUG: Property Result:", property_result)

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
            
        except Exception as e:
            print(f"DEBUG: Error in parallel evaluation: {type(e).__name__}: {str(e)}")
            raise

    async def _verify_credit_history(self) -> Dict[str, Any]:
        """
        Verifies credit history as shown in BPMN diagram.
        """
        self.process_logger.log_step("Starting Credit History Verification")
        
        try:
            loan_data = {
                'application_id': self.application.application_id,
                'client_name': self.application.client_name,
                'monthly_income': float(self.application.monthly_income),
                'monthly_expenses': float(self.application.monthly_expenses),
                'loan_amount': float(self.application.loan_amount),
                'loan_duration_years': self.application.loan_duration_years
            }
            
            print(f"DEBUG: Credit history verification data: {loan_data}")
            
            # Get result from eligibility service
            service_result = evaluate_eligibility.apply(args=[loan_data]).get()
            
            # Ensure result has the required structure
            result = {
                'meets_requirements': service_result.get('is_eligible', False),
                'credit_score': service_result.get('credit_score', 0),
                'dti_ratio': service_result.get('dti_ratio', 0),
                'evaluation_details': service_result
            }
            
            self.process_logger.log_step("Credit History Verification Complete", result)
            return result
            
        except Exception as e:
            print(f"DEBUG: Error in credit history verification: {type(e).__name__}: {str(e)}")
            print(f"DEBUG: Application attributes: {vars(self.application)}")
            # Return a failure result if there's an error
            return {
                'meets_requirements': False,
                'error': str(e),
                'evaluation_details': {}
            }

    async def _evaluate_property(self) -> Dict[str, Any]:
        """
        Evaluates property as shown in BPMN diagram.
        """
        self.process_logger.log_step("Starting Property Evaluation")
        
        # Convert loan_amount to string before adding to property_data
        loan_amount = str(self.application.loan_amount) if hasattr(self.application, 'loan_amount') else None
        
        property_data = {
            'application_id': self.application.application_id,
            'property_description': self.application.property_description,
            'loan_amount': loan_amount
        }
        
        # Add safety check for loan_amount
        if not loan_amount:
            return {
                'meets_requirements': False,
                'error': 'Missing loan amount',
                'risk_assessment': 'High'
            }
        
        # Simulate property evaluation
        await asyncio.sleep(3)
        
        # In real implementation, this would call a property evaluation service
        evaluation_result = {
            'meets_requirements': True,
            'property_value': float(loan_amount) * 1.2,
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
        
        # Check residency insurance interest
        insurance_interest = await self._check_residency_insurance_interest()
        if insurance_interest:
            await self._send_insurance_details()
        
        # Prepare agreement and verify compliance
        agreement_result = await self._prepare_reimbursement_agreement()
        verification_result = await self._verify_reimbursement_agreement(agreement_result)
        
        if verification_result['compliant']:
            notification = "Application approved and verified! Agreement is complete."
            final_status = "COMPLETED_APPLICATION"
        else:
            notification = f"Agreement verification failed: {verification_result['reason']}"
            final_status = "REJECTED"
        
        # Log notification
        self.process_logger.log_step("Notification Sent", {
            "message": notification,
            "status": final_status
        })
        
        return {
            "status": final_status,
            "notification": notification,
            "agreement_details": agreement_result.get('agreement_details', {})
        }

    async def _check_residency_insurance_interest(self) -> bool:
        """
        Prompts user about residency insurance interest.
        """
        self.process_logger.log_step("Checking Residency Insurance Interest")
        
        while True:
            response = input("\nWould you be interested in residency insurance? (yes/no): ").lower()
            if response in ['yes', 'no']:
                result = response == 'yes'
                self.process_logger.log_step("Residency Insurance Response", {
                    "interested": result
                })
                return result
            print("Please answer 'yes' or 'no'")

    async def _send_insurance_details(self):
        """
        Simulates sending insurance details to the client.
        """
        self.process_logger.log_step("Sending Insurance Details", {
            "insurance_package": "Standard Residency Coverage",
            "monthly_cost": "€45.00",
            "coverage_details": "Basic protection against fire, theft, and water damage"
        })
        await asyncio.sleep(1)  # Simulate sending delay

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

    async def _verify_reimbursement_agreement(self, agreement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifies if the reimbursement agreement meets all compliance requirements.
        Simulates checking against "accords de remboursement" database.
        """
        self.process_logger.log_step("Verifying Reimbursement Agreement")
        
        try:
            # Load verification rules
            with open('reimbursement_rules.json', 'r') as f:
                rules = json.load(f)
            
            # Extract agreement details
            monthly_payment = agreement_data['agreement_details']['monthly_payment']
            total_repayment = agreement_data['agreement_details']['total_repayment']
            duration_years = agreement_data['agreement_details']['duration_years']
            
            # Simulate verification checks
            checks = {
                "payment_schedule": monthly_payment <= rules['max_monthly_payment'],
                "duration_valid": duration_years <= rules['max_duration_years'],
                "repayment_ratio": total_repayment <= float(self.application.loan_amount) * rules['max_repayment_ratio']
            }
            
            is_compliant = all(checks.values())
            
            result = {
                "compliant": is_compliant,
                "reason": "All verification checks passed" if is_compliant else "Failed compliance checks",
                "verification_details": checks
            }
            
            self.process_logger.log_step("Reimbursement Agreement Verification Complete", result)
            return result
            
        except Exception as e:
            print(f"Error in reimbursement verification: {str(e)}")
            return {
                "compliant": False,
                "reason": f"Verification error: {str(e)}",
                "verification_details": {}
            }

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

    async def _verify_completeness(self) -> Dict[str, Any]:
        """
        Verifies the completeness of the loan application using the verification service.
        Returns a dictionary with verification results.
        """
        try:
            loan_data = {
                'application_id': self.application.application_id,
                'client_name': self.application.client_name,
                'address': self.application.address,
                'email': self.application.email,
                'phone': self.application.phone,
                'loan_amount': str(self.application.loan_amount),  # Convert Decimal to string
                'loan_duration_years': self.application.loan_duration_years,
                'property_description': self.application.property_description,
                'monthly_income': str(self.application.monthly_income),  # Convert Decimal to string
                'monthly_expenses': str(self.application.monthly_expenses)  # Convert Decimal to string
            }
            
            result = verify_completion.apply(args=[loan_data]).get()
            
            self.process_logger.log_step("Completeness Verification Result", result)
            return result
            
        except Exception as e:
            print(f"DEBUG: Error in _verify_completeness: {type(e).__name__}: {str(e)}")
            print(f"DEBUG: Loan data being prepared: {vars(self.application)}")
            raise

    async def _request_application_updates(self, missing_fields: List[str]):
        """
        Handles requesting updates for incomplete applications.
        In a real implementation, this would trigger notifications to the client.
        """
        self.process_logger.log_step("Requesting Application Updates", {
            "missing_fields": missing_fields
        })
        # Simulate waiting for updates
        await asyncio.sleep(1)

    def _finalize_process(self, final_status: str) -> Dict[str, Any]:
        """
        Finalizes the loan application process with complete summary.
        """
        process_summary = {
            "application_id": self.application.application_id,
            "final_status": final_status,
            "client_name": self.application.client_name,
            "loan_amount": str(self.application.loan_amount) if hasattr(self.application, 'loan_amount') else None,
            "verification_attempts": self.verification_attempts,
            "process_completion_time": datetime.now().isoformat()
        }
        
        self.process_logger.finalize_process(final_status, process_summary)
        return process_summary

async def main():
    """
    Main execution function that demonstrates the loan application process.
    """
    try:
        # Create sample loan application with more realistic values
        loan_application = LoanApplication(
            client_name="Alexandre Dubois",
            address="25 Avenue Montaigne, 75008 Paris, France",
            email="alexandre.dubois@email.com",
            phone="+33 6 12 34 56 78",
            loan_amount=Decimal("750000.00"),  # Reduced loan amount
            loan_duration_years=25,
            property_description="Appartement de luxe de 250m² avec terrasse panoramique...",
            monthly_income=Decimal("35000.00"),  # Current monthly income
            monthly_expenses=Decimal("8000.00")
        )
        
        # Initialize processor and start process
        processor = LoanApplicationProcessor()
        result = await processor.process_loan_application(loan_application)
        
        print("\nLoan Application Process Completed")
        print("="*50)
        print(json.dumps(result, indent=2))
        print("\nDetailed logs available in:")
        print(f"- Detailed logs: {processor.process_logger.detailed_logs_dir}")
        print(f"- JSON logs: {processor.process_logger.json_logs_dir}")
        
    except Exception as e:
        print(f"\nError during process execution: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())