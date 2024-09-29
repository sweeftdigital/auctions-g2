from django.core.exceptions import ValidationError
from django.db import models


class TagChoices(models.TextChoices):
    LUXURY = "Luxury", "Luxury"
    VINTAGE = "Vintage", "Vintage"
    DURABLE = "Durable", "Durable"
    COMPACT = "Compact", "Compact"
    PORTABLE = "Portable", "Portable"
    INNOVATIVE = "Innovative", "Innovative"
    STYLISH = "Stylish", "Stylish"
    MODERN = "Modern", "Modern"
    UNIQUE = "Unique", "Unique"
    HANDMADE = "Handmade", "Handmade"
    ECO_FRIENDLY = "Eco-friendly", "Eco-friendly"
    LIMITED = "Limited", "Limited"
    RARE = "Rare", "Rare"
    FUNCTIONAL = "Functional", "Functional"
    VERSATILE = "Versatile", "Versatile"
    CHIC = "Chic", "Chic"
    TRENDY = "Trendy", "Trendy"
    CUSTOM = "Custom", "Custom"
    SLEEK = "Sleek", "Sleek"
    LIGHTWEIGHT = "Lightweight", "Lightweight"
    SMART = "Smart", "Smart"
    ROBUST = "Robust", "Robust"
    EFFICIENT = "Efficient", "Efficient"
    INTERACTIVE = "Interactive", "Interactive"
    COLORFUL = "Colorful", "Colorful"
    ELEGANT = "Elegant", "Elegant"
    BOLD = "Bold", "Bold"
    SOFT = "Soft", "Soft"
    COMFORTABLE = "Comfortable", "Comfortable"
    BREATHABLE = "Breathable", "Breathable"
    ADJUSTABLE = "Adjustable", "Adjustable"
    MULTI_PURPOSE = "Multi-purpose", "Multi-purpose"
    QUICK = "Quick", "Quick"
    RELIABLE = "Reliable", "Reliable"
    PREMIUM = "Premium", "Premium"
    ORIGINAL = "Original", "Original"
    INTUITIVE = "Intuitive", "Intuitive"
    LUXURIOUS = "Luxurious", "Luxurious"
    WATERPROOF = "Waterproof", "Waterproof"
    WIRELESS = "Wireless", "Wireless"
    HIGH_TECH = "High-tech", "High-tech"
    ENERGY = "Energy", "Energy"
    REFRESHING = "Refreshing", "Refreshing"
    CUSTOMIZABLE = "Customizable", "Customizable"
    SAFE = "Safe", "Safe"
    AFFORDABLE = "Affordable", "Affordable"
    ARTISTIC = "Artistic", "Artistic"
    TRENDSETTING = "Trendsetting", "Trendsetting"
    CLASSIC_TAG = "Classic", "Classic"
    EFFORTLESS = "Effortless", "Effortless"
    SOPHISTICATED = "Sophisticated", "Sophisticated"
    WARM = "Warm", "Warm"
    VIBRANT = "Vibrant", "Vibrant"
    REUSABLE = "Reusable", "Reusable"
    ACCESSIBLE = "Accessible", "Accessible"
    ATTRACTIVE = "Attractive", "Attractive"
    ARTISAN = "Artisan", "Artisan"
    REFINED = "Refined", "Refined"
    GRACEFUL = "Graceful", "Graceful"
    CONTEMPORARY = "Contemporary", "Contemporary"
    NATURAL = "Natural", "Natural"
    STURDY = "Sturdy", "Sturdy"
    PLEASURABLE = "Pleasurable", "Pleasurable"
    IMPRESSIVE = "Impressive", "Impressive"
    GENEROUS = "Generous", "Generous"
    INSPIRING = "Inspiring", "Inspiring"
    WHIMSICAL = "Whimsical", "Whimsical"
    TRUSTWORTHY = "Trustworthy", "Trustworthy"
    SERENE = "Serene", "Serene"
    CAPTIVATING = "Captivating", "Captivating"
    CHARMING = "Charming", "Charming"
    NOURISHING = "Nourishing", "Nourishing"
    PASSIONATE = "Passionate", "Passionate"
    AFFECTIONATE = "Affectionate", "Affectionate"
    REWARDING = "Rewarding", "Rewarding"
    IMPACTFUL = "Impactful", "Impactful"
    RESILIENT = "Resilient", "Resilient"
    GROUNDBREAKING = "Groundbreaking", "Groundbreaking"
    OPTIMISTIC = "Optimistic", "Optimistic"
    THOUGHTFUL = "Thoughtful", "Thoughtful"
    AMBITIOUS = "Ambitious", "Ambitious"
    DYNAMIC = "Dynamic", "Dynamic"
    FEARLESS = "Fearless", "Fearless"
    SAVVY = "Savvy", "Savvy"
    TRANSFORMATIVE = "Transformative", "Transformative"


class Tag(models.Model):
    name = models.CharField(max_length=50, choices=TagChoices.choices)

    def delete(self, *args, **kwargs):
        if self.auctions.exists():
            raise ValidationError("Cannot delete tag with existing auctions.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name
