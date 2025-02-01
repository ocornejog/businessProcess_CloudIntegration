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
Once an application is complete, the system conducts two parallel evaluation processes:

1. Credit History Verification
   - Credit score assessment
   - Payment history analysis
   - Debt-to-income ratio calculation

2. Property Evaluation
   - Property value assessment
   - Location analysis
   - Risk evaluation
   - Loan-to-value ratio calculation

### Phase 3: Reimbursement Agreement
For approved applications, the system handles the agreement process:

- Generation of reimbursement schedules
- Interest rate calculations
- Agreement document preparation
- Customer review tracking
- Final approval processing

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

1. Start the service workers (in separate terminals):
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