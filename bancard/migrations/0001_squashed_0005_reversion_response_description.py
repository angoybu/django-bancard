# Generated by Django 3.2.3 on 2021-05-16 19:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [
        ("bancard", "0001_initial"),
        ("bancard", "0002_auto_20210516_0143"),
        ("bancard", "0003_auto_20210516_1912"),
        ("bancard", "0004_reversion"),
        ("bancard", "0005_reversion_response_description"),
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.BANCARD_PAYMENT_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Card",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "last4",
                    models.CharField(
                        default="",
                        editable=False,
                        max_length=4,
                        verbose_name="Last 4 digits",
                    ),
                ),
                (
                    "exp_year",
                    models.PositiveSmallIntegerField(
                        default=0, editable=False, verbose_name="Exp. year"
                    ),
                ),
                (
                    "exp_month",
                    models.PositiveSmallIntegerField(
                        default=0, editable=False, verbose_name="Exp. month"
                    ),
                ),
                (
                    "brand",
                    models.CharField(
                        blank=True,
                        default="",
                        editable=False,
                        max_length=50,
                        verbose_name="Brand",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        default="",
                        editable=False,
                        max_length=50,
                        verbose_name="Type",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        editable=False,
                        verbose_name="Is active",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        db_index=True, default=False, verbose_name="Is default"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="Created at"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated at"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Card",
                "verbose_name_plural": "Cards",
            },
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Gateway response pending"),
                            ("success", "Success"),
                            ("fail", "Fail"),
                            ("reversed", "Reversed"),
                        ],
                        db_index=True,
                        default="pending",
                        editable=False,
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        editable=False,
                        max_digits=15,
                        verbose_name="Amount",
                    ),
                ),
                (
                    "customer_ip_address",
                    models.GenericIPAddressField(
                        blank=True,
                        editable=False,
                        null=True,
                        verbose_name="User IP address",
                    ),
                ),
                (
                    "tx_description",
                    models.CharField(
                        blank=True,
                        default="",
                        editable=False,
                        max_length=250,
                        verbose_name="Description",
                    ),
                ),
                (
                    "response_description",
                    models.CharField(
                        blank=True,
                        default="",
                        editable=False,
                        max_length=150,
                        verbose_name="Description",
                    ),
                ),
                (
                    "authorization_code",
                    models.CharField(
                        default="",
                        editable=False,
                        max_length=50,
                        verbose_name="Authorization code",
                    ),
                ),
                (
                    "raw_response",
                    models.JSONField(
                        default=dict, editable=False, verbose_name="Raw response"
                    ),
                ),
                ("token", models.CharField(editable=False, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "card",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transactions",
                        to="bancard.card",
                    ),
                ),
                (
                    "payment",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.BANCARD_PAYMENT_MODEL,
                        verbose_name="Payment",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
                (
                    "risk_index",
                    models.CharField(
                        default="",
                        editable=False,
                        max_length=20,
                        verbose_name="Risk Index",
                    ),
                ),
            ],
            options={
                "verbose_name": "Transaction",
                "verbose_name_plural": "Transactions",
            },
        ),
        migrations.CreateModel(
            name="Reversion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Gateway response pending"),
                            ("success", "Success"),
                            ("fail", "Fail"),
                        ],
                        db_index=True,
                        default="pending",
                        editable=False,
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "raw_response",
                    models.JSONField(
                        default=dict, editable=False, verbose_name="Raw response"
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reversions",
                        to="bancard.transaction",
                        verbose_name="Transaction",
                    ),
                ),
                (
                    "response_description",
                    models.CharField(
                        blank=True,
                        default="",
                        editable=False,
                        max_length=150,
                        verbose_name="Description",
                    ),
                ),
            ],
            options={
                "verbose_name": "Reversion",
                "verbose_name_plural": "Reversions",
            },
        ),
    ]
