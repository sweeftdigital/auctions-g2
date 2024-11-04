# Generated by Django 5.0.7 on 2024-11-04 05:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bid", "0006_bid_idx_bid_auction_created"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bid",
            name="status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Approved", "Approved"),
                    ("Rejected", "Rejected"),
                    ("Deleted", "Deleted"),
                    ("Revoked", "Revoked"),
                    ("Canceled", "Canceled"),
                ],
                default="Pending",
                help_text="Status of the bid",
                max_length=20,
            ),
        ),
    ]
