import hashlib
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple

import requests
from django.conf import settings
from .models import Transaction


class BancardGateway:
    def __init__(self) -> None:
        self.is_test_mode: bool = settings.BANCARD_TEST_MODE
        if self.is_test_mode:
            self.pub_key: str = settings.BANCARD_TEST_PUBLIC_KEY
            self.priv_key: str = settings.BANCARD_TEST_PRIVATE_KEY
            self.base_url = "https://vpos.infonet.com.py:8888/vpos/api/0.3"
        else:
            self.pub_key: str = settings.BANCARD_PUBLIC_KEY
            self.priv_key: str = settings.BANCARD_PRIVATE_KEY
            self.base_url = "https://vpos.infonet.com.py/vpos/api/0.3"

    def perform_request(self, path: str, data: dict, method: str = "POST") -> dict:
        if method == "POST":
            res = requests.post(f"{self.base_url}{path}", json=data)
        elif method == "DELETE":
            res = requests.delete(f"{self.base_url}{path}", json=data)
        else:
            raise NotImplementedError("Method not implemented.")
        if res.status_code in (200, 201, 202, 204):
            return res.json()
        else:
            res.raise_for_status()

    def init_card_registration(
        self,
        user_id: int,
        card_id: int,
        redirect_url: str,
        user_cellphone: str = "",
        user_email: str = "",
    ) -> Optional[str]:
        """Requests Bancard vPOS service for a process ID to register a new card.
        Returns a `process_id` string.

        :param user_id: ID of user registering the card.
        :param card_id: Internal ID of card to be registered.
        :param user_cellphone: Cellphone of user registering the card.
        :param user_email: Email of user registering the card.
        :param redirect_url: URL to redirect the user after card registration.
        """

        token = hashlib.md5(
            f"{self.priv_key}{card_id}{user_id}request_new_card".encode()
        ).hexdigest()
        data = {
            "public_key": self.pub_key,
            "operation": {
                "token": token,
                "card_id": card_id,
                "user_id": user_id,
                "user_cell_phone": user_cellphone
                or settings.BANCARD_DEFAULT_USER_CELLPHONE,
                "user_mail": user_email or settings.BANCARD_DEFAULT_USER_EMAIL,
                "return_url": redirect_url,
            },
        }
        try:
            res = self.perform_request("/cards/new", data)
            if res.get("status") == "success":
                return res.get("process_id")
        except requests.RequestException:
            # TODO better error handling
            pass

    def get_user_cards(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve all cards registered by a user.

        :param user_id: ID of the user retrieving the cards.
        """

        token = hashlib.md5(
            f"{self.priv_key}{user_id}request_user_cards".encode()
        ).hexdigest()
        data = {"public_key": self.pub_key, "operation": {"token": token}}
        try:
            res = self.perform_request(f"/users/{user_id}/cards", data)
            if res.get("status") == "success":
                card_list = []
                for card in res.get("cards"):
                    exp_month, exp_year = card.get("expiration_date").split("/")
                    card_list.append(
                        {
                            "id": card.get("card_id"),
                            "last4": card.get("card_masked_number")[-4:],
                            "exp_year": int(exp_year),
                            "exp_month": int(exp_month),
                            "brand": card.get("card_brand"),
                            "type": card.get("card_type"),
                            "token": card.get("alias_token"),
                        }
                    )
                return card_list
        except requests.RequestException:
            # TODO Better error handling
            pass

    def get_user_card(self, user_id: int, card_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single card registered by a user.

        :param user_id: ID of user retrieving the card.
        :param card_id: ID of card be retrieved.
        """
        cards = self.get_user_cards(user_id)
        if not cards:
            return
        for card in cards:
            if card["id"] == card_id:
                return card

    def delete_card(self, user_id: int, card_id: int) -> bool:
        """Delete a card registered by a user.

        :param user_id: ID of user deleting the card.
        :param card_id: ID of card to be deleted.
        """
        card = self.get_user_card(user_id, card_id)
        if not card:
            return False
        token = hashlib.md5(
            f"{self.priv_key}delete_card{user_id}{card['token']}".encode()
        ).hexdigest()
        data = {
            "public_key": self.pub_key,
            "operation": {"token": token, "alias_token": card["token"]},
        }
        try:
            res = self.perform_request(f"/users/{user_id}/cards", data, method="DELETE")
            if res.get("status") == "success":
                return True
        except requests.RequestException:
            # TODO Better error handling
            return False

    @staticmethod
    def _process_transaction_response(data: dict) -> Optional[Dict[str, Any]]:
        """Processes a transaction data sent by Bancard and parses data to return
        relevant information.

        :param data: data sent by Bancard.
        """

        # Check if relevant keys exist in data
        if not ("confirmation" in data or "operation" in data):
            return {
                "is_success": False,
            }
        operation = data.get("operation", data.get("confirmation"))

        # process response
        try:
            risk_index = int(operation.get("security_information").get("risk_index"))
            if risk_index < 4:
                risk_index = "low"
            elif 4 <= risk_index <= 6:
                risk_index = "medium"
            else:
                risk_index = "high"
        except (ValueError, AttributeError):
            risk_index = None
        return {
            "tx_id": operation.get("shop_process_id"),
            "is_success": operation.get("response_code") == "00",
            "description": operation.get("response_description"),
            "amount": Decimal(operation.get("amount", 0)),
            "authorization_code": operation.get("authorization_number"),
            "customer_ip": operation.get("security_information").get("customer_ip"),
            "risk_index": risk_index,
            "token": operation.get("token"),
            "raw_response": data,
        }

    def charge_card(
        self,
        user_id: int,
        card_id: int,
        tx_id: int,
        amount: Decimal,
        description: str,
        installments: Optional[int] = None,
        additional_data: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Attempts to capture a payment.

        :param user_id: ID of user making payment.
        :param card_id: ID of card to be used for payment.
        :param tx_id: ID of current transaction.
        :param amount: amount to capture.
        :param description: capture description that will be shown to user.
        :param installments: no. of installments for payment (only for credit).
        :param additional_data: additional data to be sent (reserved for future use).
        """
        card = self.get_user_card(user_id, card_id)
        if not card:
            return
        card_token = card["token"]
        amount_str = "{:.2f}".format(amount)
        token = hashlib.md5(
            f"{self.priv_key}{tx_id}charge{amount_str}PYG{card_token}".encode()
        ).hexdigest()
        data = {
            "public_key": self.pub_key,
            "operation": {
                "token": token,
                "shop_process_id": tx_id,
                "amount": amount_str,
                "number_of_payments": installments or 1,
                "currency": "PYG",
                "additional_data": "",
                "description": description,
                "alias_token": card_token,
            },
        }
        try:
            res = self.perform_request("/charge", data)
            return self._process_transaction_response(res)
        except requests.RequestException:
            pass

    def init_single_buy(
        self,
        tx_id: int,
        amount: Decimal,
        description: str,
        return_url: str,
        cancel_url: str = None,
        zimple: bool = False,
        additional_data: str = "",
    ) -> Optional[str]:
        """Requests Bancard vPOS service for a process ID to start a single buy operation.
        Returns a `process_id` string.

        :param tx_id: ID of the ongoing transaction.
        :param amount: Amount to be captured.
        :param description: capture description that will be shown to user.
        :param return_url: URL to redirect the user after transaction is finished.
        :param cancel_url: optional URL to redirect the user if the operation is cancelled.
        :param zimple: use Zimple to capture payment instead of credit/debit card.
        :param additional_data: additional data to send to vPOS service. For Zimple operations,
        mobile phone number goes here.
        :returns: process ID to show Bancard iFrame.
        """
        amount_str = "{:.2f}".format(amount)
        token = hashlib.md5(
            f"{self.priv_key}{tx_id}{amount_str}PYG".encode()
        ).hexdigest()

        # add tx_id to return_url and cancel_url
        params = {"tx_id": tx_id}
        url_parts = list(urlparse(return_url))
        query = dict(parse_qsl(url_parts[4]))
        query.update(params)
        url_parts[4] = urlencode(query)
        return_url = urlunparse(url_parts)
        if cancel_url:
            url_parts = list(urlparse(cancel_url))
            query = dict(parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urlencode(query)
            cancel_url = urlunparse(url_parts)

        data = {
            "public_key": self.pub_key,
            "operation": {
                "token": token,
                "shop_process_id": tx_id,
                "currency": "PYG",
                "amount": amount_str,
                "additional_data": additional_data,
                "description": description,
                "return_url": return_url,
                "cancel_url": cancel_url or return_url,
            },
        }
        if zimple:
            data["operation"]["zimple"] = "S"
        try:
            res = self.perform_request("/single_buy", data)
            if res.get("status") == "success":
                return res.get("process_id")
        except requests.RequestException:
            pass

    def get_single_buy_confirmation(self, tx_id: int) -> Optional[Dict[str, Any]]:
        """Gets transaction status.

        :param tx_id: ID of transaction to confirm.
        """
        token = hashlib.md5(
            f"{self.priv_key}{tx_id}get_confirmation".encode()
        ).hexdigest()
        data = {
            "public_key": self.pub_key,
            "operation": {
                "token": token,
                "shop_process_id": tx_id,
            },
        }
        try:
            res = self.perform_request("/single_buy/confirmations", data)
            return self._process_transaction_response(res)
        except requests.RequestException:
            pass

    def rollback(self, tx_id: int) -> Tuple[bool, dict]:
        """Attempts a rollback on a captured payment.

        :param tx_id: ID of transaction on which rollback will be performed.
        :returns: Boolean indicating rollback status and vPOS response.
        """
        token = hashlib.md5(f"{self.priv_key}{tx_id}rollback0.00".encode()).hexdigest()
        data = {
            "public_key": self.pub_key,
            "operation": {"token": token, "shop_process_id": tx_id},
        }
        try:
            res = self.perform_request("/single_buy/rollback", data)
            if res.get("status") == "success":
                return True, res
            return False, res
        except requests.RequestException:
            pass
        return False, dict()

    def callback(self, data: dict):
        shop_process_id = data.get("operation").get("shop_process_id")
        tx = Transaction.objects.get(id=shop_process_id)
        amount = data.get("operation").get("amount")
        currency = data.get("operation").get("currency")
        string = f"{self.priv_key}{shop_process_id}confirm{amount}{currency}"
        token = hashlib.md5(string.encode()).hexdigest()
        if token != data.get("operation").get("token") and tx.token != data.get(
            "operation"
        ).get("token"):
            return
        return self._process_transaction_response(data)


bancard = BancardGateway()


__all__ = ["bancard"]
