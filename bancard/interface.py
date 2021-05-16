from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class BancardCard:
    """Represents a Credit/Debit card registered using Bancard vPOS."""

    id: int
    last4: str
    exp_year: int
    exp_month: int
    brand: str
    type: str
    is_default: bool


@dataclass
class PrivateChargeResponse:
    """Holds information sent from Bancard vPOS that should not be shown
    to the customer.
    """

    authorization_code: str
    risk_index: str


@dataclass
class ChargeResponse:
    """Holds information about the ongoing transaction."""

    payment_id: Optional[int]
    tx_id: int
    amount: Decimal
    status: str
    response_description: Optional[str]
    tx_datetime: datetime
    private_data: Optional[PrivateChargeResponse]
