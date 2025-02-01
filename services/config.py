import os
from typing import Dict, Any

RABBITMQ_CONFIG: Dict[str, Any] = {
    'host': os.getenv('RABBITMQ_HOST', 'localhost'),
    'port': int(os.getenv('RABBITMQ_PORT', 5672)),
    'username': os.getenv('RABBITMQ_USER', 'guest'),
    'password': os.getenv('RABBITMQ_PASSWORD', 'guest'),
}

CELERY_CONFIG: Dict[str, Any] = {
    'broker_url': f"amqp://{RABBITMQ_CONFIG['username']}:{RABBITMQ_CONFIG['password']}@{RABBITMQ_CONFIG['host']}:{RABBITMQ_CONFIG['port']}/",
    'result_backend': 'rpc://',
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    'task_track_started': True,
}

LOAN_RULES = {
    'REQUIRED_FIELDS': [
        'client_name', 'address', 'email', 'phone',
        'loan_amount', 'loan_duration_years', 'property_description',
        'monthly_income', 'monthly_expenses'
    ],
    'MIN_CREDIT_SCORE': 650,
    'MAX_DTI_RATIO': 0.43,
    'MIN_INCOME_MULTIPLIER': 3,
    'MAX_LOAN_DURATION_YEARS': 30,
}