from rest_framework import serializers

from auction.models import Auction, Bookmark, Category, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name"]


class AuctionListSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    product = serializers.CharField(source="auction_name")

    class Meta:
        model = Auction
        fields = [
            "id",
            "product",
            "status",
            "category",
            "max_price",
            "quantity",
            "start_date",
            "end_date",
        ]


class AuctionRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auction
        fields = "__all__"


class BookmarkCreateSerializer(serializers.ModelSerializer):
    auction_id = serializers.UUIDField(write_only=True)
    bookmark_id = serializers.UUIDField(source="id", read_only=True)
    user_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Bookmark
        fields = ["auction_id", "user_id", "bookmark_id"]

    @staticmethod
    def validate_auction_id(value):
        try:
            Auction.objects.get(id=value)
        except Auction.DoesNotExist:
            raise serializers.ValidationError("Auction with this ID does not exist.")
        return value

    def create(self, validated_data):
        user_id = self.context.get("user_id")
        auction_id = validated_data["auction_id"]

        if Bookmark.objects.filter(user_id=user_id, auction_id=auction_id).exists():
            raise serializers.ValidationError("This auction is already bookmarked.")

        bookmark = Bookmark.objects.create(user_id=user_id, auction_id=auction_id)
        return bookmark
