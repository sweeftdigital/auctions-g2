from django.db import models


class CategoryChoices(models.TextChoices):
    ELECTRONICS = "Electronics", "Electronics"
    CLOTHING_SHOES_ACCESSORIES = (
        "Clothing, Shoes & Accessories",
        "Clothing, Shoes & Accessories",
    )
    SPORTING_GOODS = "Sporting Goods", "Sporting Goods"
    TOYS_HOBBIES = "Toys & Hobbies", "Toys & Hobbies"
    HOME_GARDEN = "Home & Garden", "Home & Garden"
    JEWELRY_WATCHES = "Jewelry & Watches", "Jewelry & Watches"
    HEALTH_BEAUTY = "Health & Beauty", "Health & Beauty"
    BUSINESS_INDUSTRIAL = "Business & Industrial", "Business & Industrial"
    BABY_ESSENTIALS = "Baby Essentials", "Baby Essentials"
    PET_SUPPLIES = "Pet Supplies", "Pet Supplies"
    BOOKS_MOVIES_MUSIC = "Books, Movies & Music", "Books, Movies & Music"
    COLLECTIBLES_ART = "Collectibles & Art", "Collectibles & Art"
    VEHICLE_PARTS_ACCESSORIES = (
        "Vehicle Parts & Accessories",
        "Vehicle Parts & Accessories",
    )
    MUSICAL_INSTRUMENTS_GEAR = "Musical Instruments & Gear", "Musical Instruments & Gear"
    MAJOR_APPLIANCES = "Major Appliances", "Major Appliances"
    CAMPING_HIKING = "Camping & Hiking", "Camping & Hiking"
    AUTOMOTIVE = "Automotive", "Automotive"
    REAL_ESTATE = "Real Estate", "Real Estate"
    FURNITURE = "Furniture", "Furniture"
    FOOD_BEVERAGES = "Food & Beverages", "Food & Beverages"
    OFFICE_SUPPLIES = "Office Supplies", "Office Supplies"
    SURVEILLANCE_SECURITY = "Surveillance & Security", "Surveillance & Security"
    BICYCLES_ACCESSORIES = "Bicycles & Accessories", "Bicycles & Accessories"
    VIDEO_GAMES_CONSOLES = "Video Games & Consoles", "Video Games & Consoles"
    CRAFTS = "Crafts", "Crafts"
    ANTIQUES = "Antiques", "Antiques"
    FISHING_BOATING = "Fishing & Boating", "Fishing & Boating"
    OTHER = "Other", "Other"


class Category(models.Model):
    name = models.CharField(
        max_length=255, choices=CategoryChoices.choices, default=CategoryChoices.OTHER
    )

    def __str__(self):
        return self.name
