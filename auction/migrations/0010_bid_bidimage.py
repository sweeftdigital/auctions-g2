# Generated by Django 5.0.7 on 2024-10-06 15:16

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auction", "0009_alter_bookmark_options_bookmark_created_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="Bid",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("author", models.UUIDField()),
                ("offer", models.DecimalField(decimal_places=2, max_digits=20)),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Enter a detailed description of the bid",
                        null=True,
                    ),
                ),
                (
                    "delivery_fee",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        help_text="Enter the delivery fee for the bid",
                        max_digits=10,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Pending", "Pending"),
                            ("Approved", "Approved"),
                            ("Rejected", "Rejected"),
                        ],
                        default="Pending",
                        help_text="Status of the bid",
                        max_length=20,
                    ),
                ),
                (
                    "auction",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="auction.auction",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BidImage",
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
                    "image_url",
                    models.URLField(
                        blank=True, help_text="URL of the uploaded image", null=True
                    ),
                ),
                (
                    "bid",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="auction.bid",
                    ),
                ),
            ],
        ),
    ]