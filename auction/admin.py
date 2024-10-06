from django.contrib import admin

from auction.models import Auction, Bid, BidImage, Bookmark, Category, Tag


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "auction_name",
        "author",
        "status",
        "max_price",
        "start_date",
        "end_date",
        "category",
        "currency",
        "condition",
    )
    list_filter = (
        "status",
        "category",
        "accepted_bidders",
        "currency",
        "condition",
        "accepted_locations",
    )
    search_fields = (
        "auction_name",
        "description",
        "category__name",
        "author",
    )
    ordering = ("-start_date",)
    autocomplete_fields = ["tags"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "auction")
    search_fields = ("user_id", "auction__auction_name")
    ordering = ("-auction",)


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "offer",
        "status",
        "delivery_fee",
        "description",
    )
    list_filter = ("status",)
    search_fields = (
        "id",
        "description",
    )
    ordering = ("-offer",)


@admin.register(BidImage)
class BidImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bid",
        "image_url",
    )
    search_fields = (
        "bid__offer",
        "image_url",
    )
    ordering = ("-id",)
