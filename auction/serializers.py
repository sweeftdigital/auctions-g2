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


class AuctionSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    # tags = TagSerializer(many=True)
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


class BookmarkCreateSerializer(serializers.ModelSerializer):
    auction_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Bookmark
        fields = ["auction_id"]

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
