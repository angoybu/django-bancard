# django-bancard

## Introduction

This is a django extension that provides functionality to process payments with Bancard's vPOS.

## Requirements

- Django >= 3.2
- requests

## Configuration

In your `settings.py` add the following configuration:

```python
...

installed_apps = [
    ...
    'bancard',
]

...

BANCARD_PAYMENT_MODEL = "yourapp.YourPaymentModel"
BANCARD_TEST_MODE = True
BANCARD_TEST_PUBLIC_KEY = "BANCARD_STAGING_PUBLIC_KEY"
BANCARD_TEST_PRIVATE_KEY = "BANCARD_STAGING_PRIVATE_KEY"
BANCARD_PUBLIC_KEY = "BANCARD_PRODUCTION_PUBLIC_KEY"
BANCARD_PRIVATE_KEY = "BANCARD_PRODUCTION_PRIVATE_KEY"
BANCARD_DEAFAULT_USER_CELLPHONE = "BANCARD_DEFAULT_USER_CELLPHONE"
BANCARD_DEFAULT_USER_EMAIL = "BANCARD_DEFAULT_USER_EMAIL"
```

In your `urls.py` add the following to enable callback functionality for vPOS "Payment Confirmation URL":

```python
from django.urls import path, include

...

urlpatterns = [
    ...
    path("", include("bancard.urls")),
]

```

## Usage

All functionality is provided in the `bancard.operations` module.
The extension provides the following operations (parameters definitions are found in function docstrings):

- `get_default_card(user_id: int) -> Optional[BancardCard]`

    Gets the default card for user with `user_id`.

- `set_default_card(user_id: int, card_id: int) -> bool`

    Sets a default card for user with `user_id`.

- `init_card_registration(user_id: int, user_cellphone: str, user_email:str, redirect_url:str) -> str`
  
    Retrieves a `process_id` to init card registration process.

- `confirm_card_registration(user_id: int) -> Optional[BancardCard]`

    Confirms that a card has been registered to the user.

- `get_cards(user_id: int) -> List[BancardCard]`

    Gets all cards registered by user.

- `get_card(user_id: int, card_id: int) -> BancardCard`
  
    Gets a card registered by a user.

- `delete_card(user_id: int, card_id: int) -> bool`

    Deletes a card registered by a user.

- `charge_card(user_id: int, card_id: int, payment_id: int, amount: Decimal, description: str, installments: Optional[int] = None, customer_ip: Optional[str] = None) -> Optional[ChargeResponse]`

    Attempts to capture payment using a registered card.

- `init_single_buy(payment_id: int, amount: Decimal, description: str, return_url: str, cancel:url Optional[str] = None, zimple: Optional[bool] = False, additional_data: Optional[str] = "", user_id: Optional[int] = None, customer_ip: Optional[str] = "") -> Optional[str]`
  
    Gets a process_id to show vPOS Checkout form.

- `get_transaction_status(payment_id: Optional[int] = None, tx_id: Optional[int] = None) -> Optional[ChargeResponse]`

    Attempts to get a transaction status. If only payment_id is sent, the operation will check for the last transaction made related to the payment_id.

- `reverse(payment_id: int, tx_id: Optional[int] = None) -> bool`

    Attempts to reverse a charge operation.

- `callback(data: dict) -> tuple[Dict[str, Any], int]`

    Use it only as signal subject. Processes data sent by vPOS and returns an appropriate message and status code. Sends a `transaction_updated` signal informing listeners about the transaction status.

- `transaction_exists(tx_id: int) -> bool`

    Checks that a transaction exists. Useful for serializer/form validation.

Some operations return objects of the following classes:

```python
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
```
