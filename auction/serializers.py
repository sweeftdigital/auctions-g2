from django.db import IntegrityError, transaction
from django.utils import timezone
from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers

from auction.models import Auction, Bookmark, Category, Tag
from auction.models.auction import StatusChoices
from auction.models.category import CategoryChoices


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

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Check if the auction's start_date is in the future
        # and set status to "Upcoming"
        if instance.start_date > timezone.now():
            representation["status"] = "Upcoming"

        return representation


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


class AuctionPublishSerializer(CountryFieldMixin, serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    category = serializers.CharField()

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
        read_only_fields = ["id", "status", "author"]

    def validate(self, data):
        for field in self.Meta.read_only_fields:
            if field in self.initial_data:
                raise serializers.ValidationError({field: "This field is read-only."})
        return data

    def validate_start_date(self, value):
        if value.tzinfo is None:
            # If value is naive, convert it to aware
            value = timezone.make_aware(value, timezone.get_default_timezone())

        if value <= timezone.now():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value

    def validate_end_date(self, value):
        # Make sure the value is timezone-aware
        if value.tzinfo is None:
            # If value is naive, convert it to aware
            value = timezone.make_aware(value, timezone.get_default_timezone())

        start_date_str = self.initial_data.get("start_date")

        if start_date_str:
            start_date = timezone.datetime.fromisoformat(
                start_date_str.replace("Z", "+00:00")
            )
            if start_date.tzinfo is None:
                start_date = timezone.make_aware(
                    start_date, timezone.get_default_timezone()
                )

            if value <= start_date:
                raise serializers.ValidationError(
                    "End date must be after the start date."
                )

        return value

    def validate_max_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Max price must be greater than 0.")

        return value

    def validate_category(self, value):
        if value not in CategoryChoices.values:
            raise serializers.ValidationError(f"{value} is not a valid category.")
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                "Tags are required, make sure to include them."
            )
        return value

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        category_data = validated_data.pop("category")

        try:
            with transaction.atomic():
                category, created = Category.objects.get_or_create(name=category_data)
                auction = Auction.objects.create(
                    category=category, status=StatusChoices.LIVE, **validated_data
                )
                tags = {tag_data["name"] for tag_data in tags_data}
                tag_objects = [Tag.objects.get_or_create(name=name)[0] for name in tags]
                auction.tags.set(tag_objects)
        except IntegrityError:
            raise serializers.ValidationError(
                "There was an error during the creation of an auction. Please try again."
            )

        return auction

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["accepted_locations"] = (
            [country.name for country in instance.accepted_locations]
            if len(representation["accepted_locations"]) > 0
            else ["International"]
        )
        representation["tags"] = [tag.name for tag in instance.tags.all()]
        # Check if the auction's start_date is in the future
        # and set status to "Upcoming"
        if instance.start_date > timezone.now():
            representation["status"] = "Upcoming"

        return representation
