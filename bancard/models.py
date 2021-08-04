from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Card(models.Model):
    last4 = models.CharField(
        _("Last 4 digits"), max_length=4, default="", editable=False
    )
    exp_year = models.PositiveSmallIntegerField(
        _("Exp. year"), default=0, editable=False
    )
    exp_month = models.PositiveSmallIntegerField(
        _("Exp. month"), default=0, editable=False
    )
    brand = models.CharField(
        _("Brand"), max_length=50, default="", blank=True, editable=False
    )
    type = models.CharField(
        _("Type"), max_length=50, default="", blank=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        "+",
        verbose_name=_("User"),
        editable=False,
        db_index=True,
        null=True,
    )
    is_active = models.BooleanField(
        _("Is active"), default=False, editable=False, db_index=True
    )
    is_default = models.BooleanField(_("Is default"), default=False, db_index=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Card")
        verbose_name_plural = _("Cards")

    def save(self, *args, **kwargs):
        other_default = Card.objects.filter(user=self.user, is_default=True)
        if self.pk:
            other_default = other_default.exclude(pk=self.pk)
        other_default = other_default.first()
        if other_default:
            other_default.is_default = False
            other_default.save()
        super().save(*args, **kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "last4": self.last4,
            "exp_year": self.exp_year,
            "exp_month": self.exp_month,
            "brand": self.brand,
            "type": self.type,
            "is_default": self.is_default,
        }


class Transaction(models.Model):
    PENDING = "pending"
    SUCCESS = "success"
    FAIL = "fail"
    REVERSED = "reversed"
    STATUS_CHOICES = (
        (PENDING, _("Gateway response pending")),
        (SUCCESS, _("Success")),
        (FAIL, _("Fail")),
        (REVERSED, _("Reversed")),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        "+",
        null=True,
        verbose_name=_("User"),
        editable=False,
        db_index=True,
    )
    payment = models.ForeignKey(
        settings.BANCARD_PAYMENT_MODEL,
        models.SET_NULL,
        "+",
        null=True,
        verbose_name=_("Payment"),
        editable=False,
        db_index=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        editable=False,
        db_index=True,
    )
    amount = models.DecimalField(
        _("Amount"), max_digits=15, decimal_places=2, editable=False
    )
    customer_ip_address = models.GenericIPAddressField(
        _("User IP address"), null=True, blank=True, editable=False
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.SET_NULL,
        related_name="transactions",
        null=True,
        editable=False,
    )
    tx_description = models.CharField(
        _("Description"), max_length=250, default="", blank=True, editable=False
    )
    response_description = models.CharField(
        _("Description"), max_length=150, default="", blank=True, editable=False
    )
    authorization_code = models.CharField(
        _("Authorization code"), default="", max_length=50, editable=False
    )
    risk_index = models.CharField(
        _("Risk Index"), max_length=20, default="", editable=False
    )
    raw_response = models.JSONField(_("Raw response"), editable=False, default=dict)
    token = models.CharField(max_length=100, editable=False, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")


class Reversion(models.Model):
    PENDING = "pending"
    SUCCESS = "success"
    FAIL = "fail"
    STATUS_CHOICES = (
        (PENDING, _("Gateway response pending")),
        (SUCCESS, _("Success")),
        (FAIL, _("Fail")),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        editable=False,
        db_index=True,
    )
    transaction = models.ForeignKey(
        Transaction, models.CASCADE, "reversions", verbose_name=_("Transaction")
    )
    response_description = models.CharField(
        _("Description"), max_length=150, default="", blank=True, editable=False
    )
    raw_response = models.JSONField(_("Raw response"), editable=False, default=dict)

    class Meta:
        verbose_name = _("Reversion")
        verbose_name_plural = _("Reversions")

    def __str__(self):
        return _("Reversion for transaction {}.").format(self.transaction_id)
