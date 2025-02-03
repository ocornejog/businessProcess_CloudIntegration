# Loan Application Processing System

This project implements a sophisticated loan application processing system based on Business Process Model and Notation (BPMN). The system orchestrates a complete loan application workflow, from initial submission through completeness verification, eligibility assessment, and final agreement processing.

## System Overview

The system implements three main processing phases according to the BPMN specification:

### Phase 1: Completeness Verification
The system begins by ensuring all required application components are present and valid. This phase implements a verification loop where incomplete applications are returned to the applicant for updates. Key features include:

- Automatic validation of all required fields
- Maximum of three verification attempts
- Detailed feedback on missing or invalid information
- Automated notification system for required updates

### Phase 2: Parallel Eligibility Processing
Once an application is complete, the system conducts eligibility evaluation:

- Debt-to-Income (DTI) Ratio Analysis
  - Maximum allowed DTI ratio: 43%
  - Calculated as: Monthly Expenses / Monthly Income
- Credit Score Assessment
  - Minimum required score: 650

### Phase 3: Reimbursement Agreement
For approved applications, the system handles the agreement process with the following rules:

#### Reimbursement Rules
```json
{
    "max_monthly_payment": 5000.00,        // Maximum allowed monthly payment
    "max_duration_years": 30,              // Maximum loan duration
    "max_repayment_ratio": 1.6,           // Total repayment can't exceed 160% of loan
    "min_payment_buffer": 0.1,            // 10% buffer required in payment capacity
    "required_documentation": [
        "income_proof",
        "identity_verification",
        "property_assessment"
    ]
}
```

#### Residency Insurance Option
- Optional insurance offering during agreement phase
- Provides coverage for:
  - Fire damage
  - Theft protection
  - Water damage
- Monthly cost: €45.00

## Application Statuses

The system uses the following status codes throughout the process:

| Status Code | Description | Trigger Condition |
|-------------|-------------|------------------|
| RECEIVED | Initial application status | Application submitted |
| INCOMPLETE | Missing required information | Verification check fails |
| COMPLETE | All required fields present | Verification check passes |
| UNDER_REVIEW | Application in evaluation | Eligibility check started |
| REJECTED_INCOMPLETE | Final rejection status | Max verification attempts reached |
| REJECTED_INELIGIBLE | Final rejection status | Failed eligibility criteria (DTI > 43%) |
| REJECTED | Final rejection status | Failed reimbursement rules |
| PENDING_AGREEMENT | Awaiting agreement completion | Passed eligibility, preparing agreement |
| AGREEMENT_ACCEPTED | Agreement signed | Customer accepts terms |
| AGREEMENT_REJECTED | Agreement declined | Customer rejects terms |
| COMPLETED_APPLICATION | Final success status | All checks passed, agreement accepted |

## Project Structure

```
loan_processing/
├── services/
│   ├── __init__.py
│   ├── models.py           # Data models and status enums
│   ├── config.py           # System configuration
│   ├── completeness.py     # Completeness verification service
│   ├── eligibility.py      # Eligibility evaluation service
│   └── reimbursement.py    # Agreement processing service
├── process_logger.py       # Process logging system
├── main.py                 # Main execution script
└── requirements.txt        # Project dependencies
```

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Start RabbitMQ using Docker:
```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
```

## Service Configuration

The system uses RabbitMQ for message queuing with the following default configuration:

- Host: localhost
- Port: 5672
- Management Interface: http://localhost:15672
- Default Credentials: guest/guest

You can modify these settings in `services/config.py`.

## Running the System

1. Start the service workers:
```bash
# Terminal 1 - Completeness Service
celery -A services.completeness:app worker --loglevel=INFO -Q completeness

# Terminal 2 - Eligibility Service
celery -A services.eligibility:app worker --loglevel=INFO -Q eligibility

# Terminal 3 - Reimbursement Service
celery -A services.reimbursement:app worker --loglevel=INFO -Q reimbursement
```

2. Run the main application:
```bash
python main.py
```

## Testing

Run the test suite to verify pipeline functionality:
```bash
python test_reimbursement.py
```

The test suite covers:
- Completeness verification
- Eligibility criteria
- Reimbursement rules
- Insurance options
- Various status transitions

## Monitoring and Logs

The system provides comprehensive logging and monitoring capabilities:

1. Process Logs
   - Location: `loan_process_logs/detailed_logs/`
   - Format: Text files with timestamps
   - Content: Detailed process steps and decisions

2. Analysis Logs
   - Location: `loan_process_logs/json_logs/`
   - Format: JSON
   - Content: Machine-readable process data

3. RabbitMQ Monitoring
   - Access the management interface at http://localhost:15672
   - Monitor queue status and message flow
   - Track service performance

## License

This project is licensed under the MIT License - see the LICENSE file for details.