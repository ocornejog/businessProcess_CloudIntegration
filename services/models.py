from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from decimal import Decimal
from enum import Enum

class LoanStatus(Enum):
    RECEIVED = "RECEIVED"
    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING_AGREEMENT = "PENDING_AGREEMENT"
    AGREEMENT_ACCEPTED = "AGREEMENT_ACCEPTED"
    AGREEMENT_REJECTED = "AGREEMENT_REJECTED"
    FINALIZED = "FINALIZED"

@dataclass
class LoanApplication:
    client_name: str
    address: str
    email: str
    phone: str
    loan_amount: Decimal
    loan_duration_years: int
    property_description: str
    monthly_income: Decimal
    monthly_expenses: Decimal
    application_id: str = field(default_factory=lambda: f"LOAN_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    status: LoanStatus = field(default=LoanStatus.RECEIVED)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    history: List[Dict] = field(default_factory=list)
    
    def update_status(self, new_status: LoanStatus, comment: str = None):
        self.status = new_status
        self.last_updated = datetime.now()
        self.history.append({
            "timestamp": self.last_updated,
            "status": new_status,
            "comment": comment
        })