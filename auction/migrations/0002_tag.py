# Generated by Django 5.0.7 on 2024-09-29 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auction", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
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
                    "name",
                    models.CharField(
                        choices=[
                            ("Luxury", "Luxury"),
                            ("Vintage", "Vintage"),
                            ("Durable", "Durable"),
                            ("Compact", "Compact"),
                            ("Portable", "Portable"),
                            ("Innovative", "Innovative"),
                            ("Stylish", "Stylish"),
                            ("Modern", "Modern"),
                            ("Unique", "Unique"),
                            ("Handmade", "Handmade"),
                            ("Eco-friendly", "Eco-friendly"),
                            ("Limited", "Limited"),
                            ("Rare", "Rare"),
                            ("Functional", "Functional"),
                            ("Versatile", "Versatile"),
                            ("Chic", "Chic"),
                            ("Trendy", "Trendy"),
                            ("Custom", "Custom"),
                            ("Sleek", "Sleek"),
                            ("Lightweight", "Lightweight"),
                            ("Smart", "Smart"),
                            ("Robust", "Robust"),
                            ("Efficient", "Efficient"),
                            ("Interactive", "Interactive"),
                            ("Colorful", "Colorful"),
                            ("Elegant", "Elegant"),
                            ("Bold", "Bold"),
                            ("Soft", "Soft"),
                            ("Comfortable", "Comfortable"),
                            ("Breathable", "Breathable"),
                            ("Adjustable", "Adjustable"),
                            ("Multi-purpose", "Multi-purpose"),
                            ("Quick", "Quick"),
                            ("Reliable", "Reliable"),
                            ("Premium", "Premium"),
                            ("Original", "Original"),
                            ("Intuitive", "Intuitive"),
                            ("Luxurious", "Luxurious"),
                            ("Waterproof", "Waterproof"),
                            ("Wireless", "Wireless"),
                            ("High-tech", "High-tech"),
                            ("Energy", "Energy"),
                            ("Refreshing", "Refreshing"),
                            ("Customizable", "Customizable"),
                            ("Safe", "Safe"),
                            ("Affordable", "Affordable"),
                            ("Artistic", "Artistic"),
                            ("Trendsetting", "Trendsetting"),
                            ("Classic", "Classic"),
                            ("Effortless", "Effortless"),
                            ("Sophisticated", "Sophisticated"),
                            ("Warm", "Warm"),
                            ("Vibrant", "Vibrant"),
                            ("Reusable", "Reusable"),
                            ("Accessible", "Accessible"),
                            ("Attractive", "Attractive"),
                            ("Artisan", "Artisan"),
                            ("Refined", "Refined"),
                            ("Graceful", "Graceful"),
                            ("Contemporary", "Contemporary"),
                            ("Natural", "Natural"),
                            ("Sturdy", "Sturdy"),
                            ("Pleasurable", "Pleasurable"),
                            ("Impressive", "Impressive"),
                            ("Generous", "Generous"),
                            ("Inspiring", "Inspiring"),
                            ("Whimsical", "Whimsical"),
                            ("Trustworthy", "Trustworthy"),
                            ("Serene", "Serene"),
                            ("Captivating", "Captivating"),
                            ("Charming", "Charming"),
                            ("Nourishing", "Nourishing"),
                            ("Passionate", "Passionate"),
                            ("Affectionate", "Affectionate"),
                            ("Rewarding", "Rewarding"),
                            ("Impactful", "Impactful"),
                            ("Resilient", "Resilient"),
                            ("Groundbreaking", "Groundbreaking"),
                            ("Optimistic", "Optimistic"),
                            ("Thoughtful", "Thoughtful"),
                            ("Ambitious", "Ambitious"),
                            ("Dynamic", "Dynamic"),
                            ("Fearless", "Fearless"),
                            ("Savvy", "Savvy"),
                            ("Transformative", "Transformative"),
                        ],
                        max_length=50,
                    ),
                ),
            ],
        ),
    ]