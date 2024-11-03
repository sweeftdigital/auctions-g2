from django.contrib import admin

from auction.models import Auction, AuctionStatistics, Bookmark, Category, Tag
from bid.models import Bid, BidImage


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

    def get_queryset(self, request):
        # Bypass the custom manager to include all auctions
        return Auction._base_manager.all()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "id")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "auction", "auction_id")
    search_fields = ("user_id", "auction__auction_name")
    ordering = ("-auction",)


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "auction_id",
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


@admin.register(AuctionStatistics)
class AuctionStatisticsAdmin(admin.ModelAdmin):
    # Update this to use the new fields
    list_display = [
        "auction",
        "get_winner_bid_author",
        "get_top_bid_author",
        "views_count",
        "total_bids_count",
        "bookmarks_count",
    ]

    def get_winner_bid_author(self, obj):
        return obj.winner_bid.author if obj.winner_bid else None

    get_winner_bid_author.short_description = "Winner"

    def get_top_bid_author(self, obj):
        return obj.top_bid.author if obj.top_bid else None

    get_top_bid_author.short_description = "Top Bidder"
