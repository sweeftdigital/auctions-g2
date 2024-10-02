from django.contrib import admin

from auction.models import Auction, Bookmark, Category, Tag


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = (
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
    list_display = ("user_id", "auction")
    search_fields = ("user_id", "auction__auction_name")
    ordering = ("-auction",)
