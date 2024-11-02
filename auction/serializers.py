from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from auction.models import Auction, AuctionStatistics, Bookmark, Category, Tag
from auction.models.auction import StatusChoices
from auction.models.category import CategoryChoices
from auction.utils import get_currency_symbol


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name"]


class AuctionListSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    product = serializers.CharField(source="auction_name")
    tags = serializers.SerializerMethodField()
    bookmarked = serializers.BooleanField(default=False)
    top_bid = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = [
            "id",
            "author",
            "author_avatar",
            "author_nickname",
            "author_kyc_verified",
            "product",
            "status",
            "category",
            "tags",
            "max_price",
            "currency",
            "quantity",
            "start_date",
            "end_date",
            "bookmarked",
            "top_bid",
        ]

    def get_tags(self, obj):
        """
        Returns tags as a list of strings instead of returning
        them as a list of dictionaries containing (name: tag) pairs.
        """

        return [tag.name for tag in obj.tags.all()]

    def get_category(self, obj):
        category = obj.category
        return category.name if category else None

    def get_top_bid(self, obj):
        """
        Returns the formatted top bid if it exists, otherwise returns None
        """
        try:
            if hasattr(obj, "statistics") and obj.statistics.top_bid:
                return obj.statistics.top_bid
            return None
        except AuctionStatistics.DoesNotExist:
            return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Check if the auction's start_date is in the future
        # and set status to "Upcoming"
        if instance.start_date > timezone.now() and instance.status == StatusChoices.LIVE:
            representation["status"] = "Upcoming"

        # Attach currency symbol to max_price field
        currency = representation["currency"]
        max_price = representation["max_price"]
        top_bid = representation["top_bid"]
        representation["max_price"] = f"{get_currency_symbol(currency)}{max_price}"
        representation["top_bid"] = (
            f"{get_currency_symbol(currency)}{top_bid}" if top_bid is not None else None
        )

        return representation


class SellerLiveAuctionListSerializer(AuctionListSerializer):
    description = serializers.CharField()

    class Meta(AuctionListSerializer.Meta):
        fields = AuctionListSerializer.Meta.fields + ["description"]


class BookmarkListSerializer(serializers.ModelSerializer):
    auction = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ["id", "user_id", "auction"]

    def get_auction(self, obj):
        # Use the AuctionListSerializer to serialize the auction field
        auction_data = AuctionListSerializer(obj.auction, context=self.context).data

        return auction_data


class AuctionRetrieveSerializer(CountryFieldMixin, serializers.ModelSerializer):
    accepted_locations = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()
    bookmarked = serializers.BooleanField(default=False)
    bookmark_id = serializers.UUIDField(read_only=True, allow_null=True)
    has_bid = serializers.BooleanField(default=False)

    class Meta:
        model = Auction
        fields = "__all__"

    def get_accepted_locations(self, obj):
        return [country.name for country in obj.accepted_locations]

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    # Option 1 implementation (uncomment if using)
    def get_category(self, obj):
        category = obj.category
        return category.name if category else None

    def get_statistics(self, obj):
        if obj.status == StatusChoices.DRAFT:
            return None
        return {
            "winner_bid": obj.statistics.winner_bid,
            "winner_bid_author": obj.statistics.winner_bid_author,
            "top_bid": obj.statistics.top_bid,
            "top_bid_author": obj.statistics.top_bid_author,
            "views_count": obj.statistics.views_count,
            "total_bids_count": obj.statistics.total_bids_count,
            "bookmarks_count": obj.statistics.bookmarks_count,
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Check if the auction's start_date is in the future
        # and set status to "Upcoming"
        if instance.start_date > timezone.now() and instance.status == StatusChoices.LIVE:
            representation["status"] = "Upcoming"

        # Attach currency symbol to max_price field
        currency = representation["currency"]
        max_price = representation["max_price"]
        representation["max_price"] = f"{get_currency_symbol(currency)}{max_price}"

        # Omit statistics field if the auction has status of draft
        if instance.status == StatusChoices.DRAFT:
            representation.pop("statistics", None)
        else:
            winner_bid = representation["statistics"]["winner_bid"]
            top_bid = representation["statistics"]["top_bid"]

            if winner_bid is not None:
                representation["statistics"][
                    "winner_bid"
                ] = f"{get_currency_symbol(currency)}{winner_bid}"
            if top_bid is not None:
                representation["statistics"][
                    "top_bid"
                ] = f"{get_currency_symbol(currency)}{top_bid}"

        return representation


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
            raise NotFound()
        return value

    def create(self, validated_data):
        user_id = self.context.get("user_id")
        auction_id = validated_data["auction_id"]

        if Bookmark.objects.filter(user_id=user_id, auction_id=auction_id).exists():
            raise serializers.ValidationError(_("This auction is already bookmarked."))

        try:
            with transaction.atomic():
                bookmark = Bookmark.objects.create(user_id=user_id, auction_id=auction_id)
                AuctionStatistics.objects.filter(auction_id=auction_id).update(
                    bookmarks_count=F("bookmarks_count") + 1
                )

                return bookmark
        except IntegrityError:
            raise serializers.ValidationError(
                "Failed to create bookmark. Please try_again."
            )
        except Exception as e:
            raise serializers.ValidationError(f"An unexpected error occurred: {str(e)}")


class BaseAuctionSerializer(CountryFieldMixin, serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    category = serializers.CharField()

    class Meta:
        model = Auction
        fields = [
            "id",
            "author",
            "author_avatar",
            "author_nickname",
            "author_kyc_verified",
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
        read_only_fields = [
            "id",
            "status",
            "author",
            "author_nickname",
            "author_avatar",
            "author_kyc_verified",
        ]

    def validate(self, data):
        for field in self.Meta.read_only_fields:
            if field in self.initial_data:
                raise serializers.ValidationError({field: _("This field is read-only.")})
        return data

    def validate_max_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Max price must be greater than 0."))
        return value

    def validate_category(self, value):
        if value not in CategoryChoices.values:
            raise serializers.ValidationError(_("Invalid category."))
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                _("Tags are required, make sure to include them.")
            )
        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["accepted_locations"] = (
            [country.name for country in instance.accepted_locations]
            if len(representation["accepted_locations"]) > 0
            else ["International"]
        )
        representation["tags"] = [tag.name for tag in instance.tags.all()]

        if instance.start_date > timezone.now() and instance.status != "Draft":
            representation["status"] = "Upcoming"

        # Attach currency symbol to max_price field
        currency = representation["currency"]
        max_price = representation["max_price"]
        representation["max_price"] = f"{get_currency_symbol(currency)}{max_price}"

        return representation


class AuctionSaveSerializer(BaseAuctionSerializer):
    def validate_start_date(self, value):
        if value.tzinfo is None:
            # If value is naive, convert it to aware
            value = timezone.make_aware(
                value, timezone.get_default_timezone()
            )  # pragma: no cover

        if value <= timezone.now():
            raise serializers.ValidationError(_("Start date cannot be in the past."))
        return value

    def validate_end_date(self, value):
        if value.tzinfo is None:
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
                    _("End date must be after the start date.")
                )

        return value

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        category_data = validated_data.pop("category")

        try:
            with transaction.atomic():
                tags = {tag_data["name"] for tag_data in tags_data}
                tag_objects = [Tag.objects.get_or_create(name=name)[0] for name in tags]
                category, created = Category.objects.get_or_create(name=category_data)
                auction = Auction.objects.create(
                    category=category,
                    **validated_data,
                )
                AuctionStatistics.objects.create(auction=auction)
                auction.tags.set(tag_objects)

        except IntegrityError:
            raise serializers.ValidationError(
                _(
                    "There was an error during the creation of an auction. Please try again."
                )
            )

        return auction


class BulkDeleteAuctionSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="List of auction UUIDs to delete.",
    )


class AuctionUpdateSerializer(BaseAuctionSerializer):
    def validate(self, data):
        data = super().validate(data)
        instance = self.instance

        # Forbid updates of certain fields if auction has started
        if instance.start_date <= timezone.now():
            raise serializers.ValidationError(
                _("Cannot modify core auction parameters after the auction has started.")
            )

        # Don't allow updates if auction has ended
        if instance.end_date <= timezone.now():
            raise serializers.ValidationError(
                _("Cannot update auction that has already ended.")
            )

        return data

    def validate_start_date(self, value):
        if value.tzinfo is None:
            # If value is naive, convert it to aware
            value = timezone.make_aware(
                value, timezone.get_default_timezone()
            )  # pragma: no cover

        if value <= timezone.now():
            raise serializers.ValidationError(_("Start date cannot be in the past."))
        elif value >= self.instance.end_date:
            raise serializers.ValidationError(_("End date must be after the start date."))

        return value

    def validate_end_date(self, value):
        # Make sure the value is timezone-aware
        if value.tzinfo is None:
            value = timezone.make_aware(value, timezone.get_default_timezone())

        # Check if end date is after start date
        if value <= self.instance.start_date:
            raise serializers.ValidationError(_("End date must be after the start date."))

        return value

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags", None)
        category_data = validated_data.pop("category", None)

        try:
            with transaction.atomic():
                # Update category if provided
                if category_data:
                    category, created = Category.objects.get_or_create(name=category_data)
                    instance.category = category

                # Update tags if provided
                if tags_data is not None:
                    tags = {tag_data["name"] for tag_data in tags_data}
                    tag_objects = [
                        Tag.objects.get_or_create(name=name)[0] for name in tags
                    ]
                    instance.tags.set(tag_objects)

                # Update other fields
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)

                instance.save()

        except IntegrityError:
            raise serializers.ValidationError(
                _(
                    "There was an error during the update of the auction. Please try again."
                )
            )

        return instance
