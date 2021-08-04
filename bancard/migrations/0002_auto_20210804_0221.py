# Generated by Django 3.2.3 on 2021-08-04 02:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.BANCARD_PAYMENT_MODEL),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("bancard", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="card",
            name="user",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="payment",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.BANCARD_PAYMENT_MODEL,
                verbose_name="Payment",
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="user",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
    ]
