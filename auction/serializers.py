from rest_framework import serializers

from auction.models import Auction, Category, Tag


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
