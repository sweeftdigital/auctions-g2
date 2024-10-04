from django_countries.serializers import CountryFieldMixin
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


class BaseAuctionListSerializer(serializers.ModelSerializer):
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
            "currency",
            "quantity",
            "start_date",
            "end_date",
        ]


class BuyerAuctionListSerializer(BaseAuctionListSerializer):
    pass


class SellerAuctionListSerializer(BaseAuctionListSerializer):
    tags = serializers.SerializerMethodField()

    class Meta(BaseAuctionListSerializer.Meta):
        fields = BaseAuctionListSerializer.Meta.fields + ["tags"]

    def get_tags(self, obj):
        """
        Returns tags as a list of strings instead of returning
        them as a list of dictionaries containing (name: tag) pairs.
        """

        return [tag.name for tag in obj.tags.all()]


class BookmarkListSerializer(serializers.ModelSerializer):
    auction = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ["id", "user_id", "auction"]

    def get_auction(self, obj):
        auction = obj.auction
        return {
            "id": auction.id,
            "product": auction.auction_name,
            "status": auction.status,
            "category": CategorySerializer(auction.category).data,
            "max_price": auction.max_price,
            "currency": auction.currency,
            "quantity": auction.quantity,
            "start_date": auction.start_date,
            "end_date": auction.end_date,
        }


class AuctionRetrieveSerializer(CountryFieldMixin, serializers.ModelSerializer):
    accepted_locations = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = "__all__"

    def get_accepted_locations(self, obj):
        return [country.name for country in obj.accepted_locations]

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]


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


class AuctionCreateSerializer(CountryFieldMixin, serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    category = CategorySerializer()

    class Meta:
        model = Auction
        fields = [
            "id",
            "author",
            "auction_name",
            "description",
            "category",
            "start_date",
            "end_date",
            "max_price",
            "quantity",
            "accepted_bidders",
            "accepted_locations",
            "tags",
            "status",
            "currency",
            "custom_fields",
            "condition",
        ]
        read_only_fields = ["id", "status"]

    def validate_end_date(self, value):
        start_date = self.initial_data.get("start_date")
        if isinstance(start_date, str):
            start_date = serializers.DateField().to_internal_value(start_date)

        if value <= start_date:
            raise serializers.ValidationError("End date must be after the start date.")
        return value

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        category_data = validated_data.pop("category")

        # Get or create the category directly in the create method
        category_name = category_data["name"]
        category, created = Category.objects.get_or_create(name=category_name)

        # Create the auction instance
        auction = Auction.objects.create(category=category, **validated_data)

        # Handle tags
        tags = {tag_data["name"] for tag_data in tags_data}
        tag_objects = [Tag.objects.get_or_create(name=name)[0] for name in tags]
        auction.tags.set(tag_objects)

        return auction
