# Generated by Django 3.2.3 on 2021-05-16 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bancard", "0004_reversion"),
    ]

    operations = [
        migrations.AddField(
            model_name="reversion",
            name="response_description",
            field=models.CharField(
                blank=True,
                default="",
                editable=False,
                max_length=150,
                verbose_name="Description",
            ),
        ),
    ]