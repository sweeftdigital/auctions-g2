# Generated by Django 5.0.7 on 2024-10-02 09:05

import django_countries.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("auction", "0006_alter_auction_accepted_locations"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auction",
            name="accepted_locations",
            field=django_countries.fields.CountryField(
                blank=True, max_length=746, multiple=True
            ),
        ),
    ]