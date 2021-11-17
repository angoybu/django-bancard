from decimal import Decimal
from typing import Optional, List, Tuple, Any, Dict

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy

from .gateway import bancard
from .interface import BancardCard, PrivateChargeResponse, ChargeResponse
from .models import Card, Transaction, Reversion
from .signals import transaction_updated


__all__ = [
    "get_default_card",
    "set_default_card",
    "init_card_registration",
    "confirm_card_registration",
    "get_cards",
    "get_card",
    "delete_card",
    "charge_card",
    "init_single_buy",
    "get_transaction_status",
    "reverse",
    "callback",
]


def get_default_card(user_id: int) -> Optional[BancardCard]:
    """Gets the default card for user with `user_id`.

    :param user_id: ID of user retrieving the card.
    """
    try:
        card = Card.objects.get(user__pk=user_id, is_default=True)
    except Card.DoesNotExist:
        return
    return BancardCard(**card.to_dict())


def set_default_card(user_id: int, card_id: int) -> bool:
    """Sets a default card for user with `user_id`.

    :param user_id: ID of user who owns the card.
    :param card_id: ID of card to set default.
    """
    other_default = Card.objects.filter(user__pk=user_id).exclude(pk=card_id).first()
    if other_default:
        other_default.is_default = False
        other_default.save()
    try:
        card = Card.objects.get(user__pk=user_id, pk=card_id)
    except Card.DoesNotExist:
        return False
    card.is_default = True
    card.save()
    return True


def init_card_registration(
    user_id: int, user_cellphone: str, user_email: str, redirect_url: str
) -> Optional[str]:
    """Retrieves a `process_id` to init card registration process.

    :param user_id: ID of user registering the card
    :param user_cellphone: Cellphone of user registering the card
    :param user_email: Email of user registering the card
    :param redirect_url: URL to redirect the user after card registration.
    """
    try:
        user = get_user_model().objects.get(pk=user_id)
    except get_user_model().DoesNotExist:
        return
    default_card = get_default_card(user_id)
    card = Card.objects.create(user=user, is_default=not default_card)
    return bancard.init_card_registration(
        user_id, card.id, redirect_url, user_cellphone, user_email
    )


def confirm_card_registration(user_id: int) -> Optional[BancardCard]:
    """Confirms that a card has been registered by the user.

    :param user_id: ID of user who registered the card.
    """
    card = Card.objects.filter(user__pk=user_id, is_active=False).last()
    if not card:
        return
    vpos_card = bancard.get_user_card(user_id, card.id)
    if not vpos_card:
        return
    card.last4 = vpos_card["last4"]
    card.exp_year = vpos_card["exp_year"]
    card.exp_month = vpos_card["exp_month"]
    card.brand = vpos_card["brand"]
    card.type = vpos_card["type"]
    card.is_active = True
    card.save()
    return BancardCard(**card.to_dict())


def get_cards(user_id: int) -> List[BancardCard]:
    """Gets all cards registered by a user.

    :param user_id: ID of user retrieving the cards.
    """
    cards = Card.objects.filter(user__id=user_id, is_active=True)
    return [BancardCard(**card.to_dict()) for card in cards]


def get_card(user_id: int, card_id: int) -> Optional[BancardCard]:
    """Gets a card registered by user.

    :param user_id: ID of the user retrieving the card.
    :param card_id: ID of card to be retrieved.
    """
    try:
        return BancardCard(**Card.objects.get(user__id=user_id, pk=card_id).to_dict())
    except Card.DoesNotExist:
        pass


def delete_card(user_id: int, card_id: int) -> bool:
    """Deletes a card registered by a user.

    :param user_id: ID of user deleting the card.
    :param card_id: ID of card to be deleted.
    """
    try:
        card = Card.objects.get(user__id=user_id, pk=card_id)
    except Card.DoesNotExist:
        return False
    deleted = bancard.delete_card(user_id, card_id)
    if deleted:
        card.delete()
        return True
    return False


def _update_transaction(tx: Transaction, gw_response: dict):
    """Updates the transaction with data sent from vPOS.

    :param tx: Transaction instance to be updated.
    :param gw_response: data from vPOS.
    """
    tx.status = (
        Transaction.SUCCESS if gw_response.get("is_success") else Transaction.FAIL
    )
    tx.response_description = gw_response.get("description") or ""
    tx.authorization_code = gw_response.get("authorization_code") or ""
    tx.risk_index = gw_response.get("risk_index") or ""
    tx.token = gw_response.get("token") or ""
    tx.raw_response = gw_response.get("raw_response") or {}


def _make_charge_response(tx: Transaction) -> ChargeResponse:
    """Create a Charge response instance from transaction.

    :param tx: Transaction instance.
    """
    private_res = PrivateChargeResponse(
        authorization_code=tx.authorization_code, risk_index=tx.risk_index
    )
    return ChargeResponse(
        payment_id=tx.payment_id if tx.payment_id else None,
        tx_id=tx.id,
        amount=tx.amount,
        status=tx.status,
        response_description=tx.response_description,
        tx_datetime=tx.created_at,
        private_data=private_res,
    )


def charge_card(
    user_id: int,
    card_id: int,
    payment_id: int,
    amount: Decimal,
    description: str,
    installments: Optional[int] = None,
    customer_ip: Optional[str] = None,
) -> Optional[ChargeResponse]:
    """Attempts to capture payment using a registered card.

    :param user_id: ID of user making the payment.
    :param card_id: ID of card to be used for payment.
    :param payment_id: ID of payment to which the transaction will be attached.
    :param amount: amount to be captured.
    :param description: description of the current capture transaction.
    :param installments: number of installments for payment (only valid for credit card).
    :param customer_ip: IP Address of visitor.
    """
    try:
        card = Card.objects.get(user__id=user_id, pk=card_id)
    except Card.DoesNotExist:
        return
    gw_card = bancard.get_user_card(user_id, card_id)
    if not gw_card:
        return
    tx = Transaction.objects.create(
        user_id=user_id,
        payment_id=payment_id,
        amount=amount,
        customer_ip_address=customer_ip,
        card=card,
        tx_description=description,
    )
    response = bancard.charge_card(
        user_id, card_id, tx.id, amount, description, installments
    )
    if response:
        _update_transaction(tx, response)
    else:
        tx.status = Transaction.FAIL
    tx.save()
    return _make_charge_response(tx)


def init_single_buy(
    payment_id: int,
    amount: Decimal,
    description: str,
    return_url: str,
    cancel_url: Optional[str] = None,
    zimple: Optional[bool] = False,
    additional_data: Optional[str] = "",
    user_id: Optional[str] = "",
    customer_ip: Optional[str] = "",
) -> Optional[str]:
    tx = Transaction.objects.create(
        user_id=user_id,
        payment_id=payment_id,
        amount=amount,
        customer_ip_address=customer_ip,
        tx_description=description,
    )
    return bancard.init_single_buy(
        tx.id, amount, description, return_url, cancel_url, zimple, additional_data
    )


def get_transaction_status(
    payment_id: int, tx_id: Optional[int] = None
) -> Optional[ChargeResponse]:
    """Attempts to get a transaction status.

    If no `tx_id` is provided, the operation will check for the last transaction
    with `pending` status related to `payment_id`.

    :param payment_id: ID of payment on which to check status.
    :param tx_id: ID of transaction on which to check status.
    """

    if tx_id:
        try:
            tx = Transaction.objects.get(id=tx_id)
        except Transaction.DoesNotExist:
            return
    else:
        tx = Transaction.objects.filter(
            status=Transaction.PENDING, payment_id=payment_id
        ).last()
        if not tx:
            return
    if tx.status in (Transaction.SUCCESS, Transaction.FAIL, Transaction.REVERSED):
        return _make_charge_response(tx)
    gw_response = bancard.get_single_buy_confirmation(tx.id)
    if gw_response:
        _update_transaction(tx, gw_response)
    else:
        tx.status = Transaction.FAIL
    tx.save()
    return _make_charge_response(tx)


def reverse(payment_id: int, tx_id: Optional[int] = None) -> bool:
    """Attempts to reverse a charge operation.

    If no `tx_id` is provided, the reverse operation will be performed on the
    last successful CAPTURE transaction related to the `payment_id`.

    :param payment_id: ID of payment on which to perform reversion.
    :param tx_id: ID of transaction on which to perform reversion.
    """
    if tx_id:
        try:
            tx = Transaction.objects.get(id=tx_id)
        except Transaction.DoesNotExist:
            return False
    else:
        tx = Transaction.objects.filter(
            status=Transaction.SUCCESS, payment_id=payment_id
        ).last()
        if not tx:
            return False

    reversion = Reversion.objects.create(transaction=tx)

    # only transactions performed on same date can be rolled back.
    now = timezone.now()
    if now.date() > tx.created_at.date():
        reversion.status = Reversion.FAIL
        reversion.response_description = gettext_lazy(
            "Only transactions performed on same date can be rolled back."
        )
        reversion.save()
        return False
    is_success, vpos_response = bancard.rollback(tx.id)
    reversion.status = Reversion.SUCCESS if is_success else Reversion.FAIL
    reversion.raw_response = vpos_response
    try:
        message = vpos_response["messages"][0]
    except (KeyError, IndexError):
        pass
    else:
        reversion.response_description = message.get("dsc", "")
    tx.status = Transaction.REVERSED if is_success else tx.status
    reversion.save()
    tx.save()
    return is_success


def callback(data: dict) -> Tuple[Dict[str, Any], int]:
    """Handles data from bancard to the callback URL that was set in business configuration.

    :param data: data sent from Bancard vPOS.
    :returns: tuple with message and status for Bancard vPOS.
    """
    response = bancard.callback(data)
    if response:
        try:
            tx = Transaction.objects.get(id=response["tx_id"])
        except Transaction.DoesNotExist:
            pass
        else:
            _update_transaction(tx, response)
            tx.save()
            transaction_updated.send(
                sender=callback, response=_make_charge_response(tx)
            )
            return {"status": "success"}, 200
    return {"status": "fail"}, 400
