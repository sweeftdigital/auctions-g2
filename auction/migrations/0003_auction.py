# Generated by Django 5.0.7 on 2024-09-29 15:45

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auction", "0002_tag"),
    ]

    operations = [
        migrations.CreateModel(
            name="Auction",
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
                ("auction_name", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("max_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("quantity", models.PositiveIntegerField(default=1)),
                (
                    "accepted_bidders",
                    models.CharField(
                        choices=[
                            ("Company", "Company"),
                            ("Individual", "Individual"),
                            ("Both", "Both"),
                        ],
                        default="Both",
                        max_length=20,
                    ),
                ),
                (
                    "accepted_locations",
                    models.CharField(
                        choices=[
                            ("My Location", "My Location"),
                            ("International", "International"),
                        ],
                        default="My Location",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("draft", "Draft"),
                            ("completed", "Completed"),
                            ("canceled", "Canceled"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        choices=[("GEL", "GEL"), ("USD", "USD"), ("EUR", "EUR")],
                        default="GEL",
                        max_length=3,
                    ),
                ),
                ("custom_fields", models.JSONField(blank=True, null=True)),
                ("winner", models.UUIDField(blank=True, null=True)),
                (
                    "winner_bid_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "top_bid",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "condition",
                    models.CharField(
                        choices=[
                            ("New", "New"),
                            ("Open box", "Open box"),
                            ("Excellent", "Excellent"),
                            ("Very Good", "Very Good"),
                            ("Good", "Good"),
                            ("Used", "Used"),
                            ("For parts or not working", "For parts or not working"),
                        ],
                        default="New",
                        max_length=50,
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="auction.category"
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(related_name="auctions", to="auction.tag"),
                ),
            ],
        ),
    ]
