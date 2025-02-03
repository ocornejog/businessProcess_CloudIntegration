# concurrent_test.py
import asyncio
import random
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
import json
from pathlib import Path
import time

from services.models import LoanApplication, LoanStatus
from main import LoanApplicationProcessor

class LoanApplicationGenerator:
    """
    Generates diverse loan applications for testing purposes.
    Creates applications with varying characteristics to test different scenarios.
    """
    def __init__(self):
        # Define possible values for generating diverse applications
        self.first_names = ["Alexandre", "Marie", "Jean", "Sophie", "Pierre", "Claire"]
        self.last_names = ["Dubois", "Martin", "Bernard", "Petit", "Robert", "Richard"]
        self.cities = ["Paris", "Lyon", "Marseille", "Bordeaux", "Toulouse", "Nice"]
        
        # Property types for varied scenarios
        self.property_types = [
            "Appartement de luxe",
            "Maison individuelle",
            "Loft moderne",
            "Propriété historique",
            "Penthouse vue mer",
            "Villa contemporaine"
        ]

    def generate_application(self, application_index: int) -> LoanApplication:
        """
        Creates a unique loan application with randomized but realistic values.
        Each application has different characteristics to test various scenarios.
        """
        # Generate a unique name combination
        client_name = f"{random.choice(self.first_names)} {random.choice(self.last_names)}"
        
        # Create a realistic property description
        property_type = random.choice(self.property_types)
        city = random.choice(self.cities)
        
        # Generate realistic financial values with some variation
        # Base loan amount between 200k and 800k for more realistic scenarios
        base_loan_amount = Decimal(str(random.randint(200000, 800000)))
        
        # Monthly income that satisfies the income multiplier rule (loan_amount / annual_income <= 3)
        min_annual_income = base_loan_amount / Decimal('3')
        min_monthly_income = min_annual_income / Decimal('12')
        
        # Add some randomness to make each application unique but still eligible
        monthly_income = min_monthly_income * Decimal(str(random.uniform(1.0, 1.5)))
        monthly_expenses = monthly_income * Decimal(str(random.uniform(0.2, 0.35)))  # Keep DTI ratio reasonable
        
        return LoanApplication(
            client_name=client_name,
            address=f"{random.randint(1, 150)} Rue {random.choice(['de la Paix', 'Victor Hugo', 'Saint-Honoré'])}, {city}",
            email=f"{client_name.lower().replace(' ', '.')}@email.com",
            phone=f"+33 {random.randint(600000000, 699999999)}",
            loan_amount=base_loan_amount,
            loan_duration_years=random.choice([15, 20, 25, 30]),
            property_description=f"{property_type} de {random.randint(60, 300)}m² à {city}",
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses
        )

class ConcurrentProcessingTester:
    """
    Manages concurrent processing of multiple loan applications.
    Tracks performance metrics and ensures proper handling of parallel requests.
    """
    def __init__(self, num_applications: int, batch_size: int = 50):
        self.num_applications = num_applications
        self.batch_size = min(batch_size, num_applications)  # Ensure batch size doesn't exceed total applications
        self.generator = LoanApplicationGenerator()
        self.results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

    async def process_application(self, application: LoanApplication) -> Dict[str, Any]:
        """
        Processes a single loan application and tracks its execution time.
        Returns detailed results including timing information.
        """
        processor = LoanApplicationProcessor()
        start_time = time.time()
        
        try:
            result = await processor.process_loan_application(application)
            processing_time = time.time() - start_time
            
            return {
                'application_id': application.application_id,
                'client_name': application.client_name,
                'loan_amount': str(application.loan_amount),
                'status': result['final_status'],
                'processing_time': processing_time,
                'success': True
            }
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                'application_id': application.application_id,
                'client_name': application.client_name,
                'error': str(e),
                'processing_time': processing_time,
                'success': False
            }

    async def run_concurrent_test(self):
        """
        Executes the concurrent processing test and generates a comprehensive report.
        Handles multiple applications simultaneously and tracks overall performance.
        """
        print(f"\nStarting concurrent processing test with {self.num_applications} applications...")
        self.start_time = time.time()
        
        # Generate all applications upfront
        applications = [
            self.generator.generate_application(i)
            for i in range(self.num_applications)
        ]
        
        # Process applications in batches for better performance
        for i in range(0, len(applications), self.batch_size):
            batch = applications[i:i + self.batch_size]
            tasks = [self.process_application(app) for app in batch]
            batch_results = await asyncio.gather(*tasks)
            self.results.extend(batch_results)
            
            # Print progress
            processed = len(self.results)
            print(f"Processed {processed}/{self.num_applications} applications...")
        
        self.end_time = time.time()
        
        # Generate and save test report
        self._generate_test_report()

    def _generate_test_report(self):
        """
        Creates a detailed report of the concurrent processing test results.
        Includes statistics and performance metrics.
        """
        total_time = self.end_time - self.start_time
        successful_applications = [r for r in self.results if r.get('success', False)]
        failed_applications = [r for r in self.results if not r.get('success', False)]
        
        # Calculate statistics
        processing_times = [r['processing_time'] for r in self.results]
        avg_processing_time = sum(processing_times) / len(processing_times)
        max_processing_time = max(processing_times)
        min_processing_time = min(processing_times)
        
        # Create report
        report = {
            'test_summary': {
                'total_applications': self.num_applications,
                'successful_applications': len(successful_applications),
                'failed_applications': len(failed_applications),
                'total_processing_time': total_time,
                'average_processing_time': avg_processing_time,
                'max_processing_time': max_processing_time,
                'min_processing_time': min_processing_time,
                'throughput': self.num_applications / total_time
            },
            'application_results': self.results
        }
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = Path(f'test_reports/concurrent_test_{timestamp}.json')
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\nConcurrent Processing Test Results:")
        print("="*50)
        print(f"Total Applications Processed: {self.num_applications}")
        print(f"Successful Applications: {len(successful_applications)}")
        print(f"Failed Applications: {len(failed_applications)}")
        print(f"Total Processing Time: {total_time:.2f} seconds")
        print(f"Average Processing Time: {avg_processing_time:.2f} seconds")
        print(f"Maximum Processing Time: {max_processing_time:.2f} seconds")
        print(f"Minimum Processing Time: {min_processing_time:.2f} seconds")
        print(f"Throughput: {self.num_applications / total_time:.2f} applications/second")
        print(f"\nDetailed report saved to: {report_path}")

async def main():
    """
    Main execution function that runs the concurrent processing test.
    Allows specification of the number of concurrent applications to process.
    """
    # Number of concurrent applications to process
    num_applications = 100  # Increased number of applications
    batch_size = 50  # Process 50 applications at a time
    
    # Create and run the tester
    tester = ConcurrentProcessingTester(num_applications, batch_size)
    await tester.run_concurrent_test()

if __name__ == "__main__":
    asyncio.run(main())