# Generated by Django 5.0.7 on 2024-10-31 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auction", "0012_auctionstatistics_bookmarks_count"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="auction",
            index=models.Index(fields=["author"], name="auction_auc_author_8c26f5_idx"),
        ),
        migrations.AddIndex(
            model_name="auction",
            index=models.Index(
                fields=["start_date", "end_date"], name="auction_auc_start_d_c1f3eb_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="auction",
            index=models.Index(fields=["status"], name="auction_auc_status_459e17_idx"),
        ),
        migrations.AddIndex(
            model_name="auction",
            index=models.Index(
                fields=["created_at"], name="auction_auc_created_0f244a_idx"
            ),
        ),
    ]