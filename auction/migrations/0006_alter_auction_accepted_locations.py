# Generated by Django 5.0.7 on 2024-10-01 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auction", "0005_alter_category_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auction",
            name="accepted_locations",
            field=models.CharField(default="International"),
        ),
    ]
