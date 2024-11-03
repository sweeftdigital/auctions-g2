from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from auction.models.auction import AuctionStatistics
from auction.utils import get_currency_symbol
from bid.models.bid import Bid, BidImage


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = "__all__"


class BidImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidImage
        fields = ["image_url"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        try:
            if instance.image_url:
                representation["image_url"] = instance.image_url.url
        except Exception as e:
            print(f"Error processing image URL for bid image {instance.id}: {e}")
        return representation


class BidListSerializer(serializers.ModelSerializer):
    images = BidImageSerializer(many=True, read_only=True)
    auction_status = serializers.SerializerMethodField(read_only=True)
    auction_author_nickname = serializers.SerializerMethodField(read_only=True)
    auction_max_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Bid
        fields = [
            "id",
            "author",
            "author_nickname",
            "author_avatar",
            "author_kyc_verified",
            "auction",
            "auction_status",
            "auction_author_nickname",
            "auction_max_price",
            "offer",
            "description",
            "delivery_fee",
            "status",
            "images",
        ]

    def get_auction_status(self, obj):
        # Only include auction status if we're listing all bids of seller (no auction_id in context)
        if self.context.get("auction_id") is None:
            return obj.auction.status
        return None

    def get_auction_author_nickname(self, obj):
        # Only include auction author nickname if we're listing all bids of seller (no auction_id in context)
        if self.context.get("auction_id") is None:
            return obj.auction.author_nickname
        return None

    def get_auction_max_price(self, obj):
        # Only include auction author nickname if we're listing all bids of seller (no auction_id in context)
        if self.context.get("auction_id") is None:
            currency = obj.auction.currency
            max_price = obj.auction.max_price
            return f"{get_currency_symbol(currency)}{max_price}"
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        currency = instance.auction.currency
        offer = representation["offer"]
        representation["offer"] = f"{get_currency_symbol(currency)}{offer}"

        delivery_fee = representation.get("delivery_fee")
        if delivery_fee:
            representation["delivery_fee"] = (
                f"{get_currency_symbol(currency)}{delivery_fee}"
            )

        image_urls = [
            image.image_url.url for image in instance.images.all() if image.image_url
        ]
        representation["images"] = image_urls

        # Remove fields with None values from representation if auction_id is not in context
        for field in ["auction_status", "auction_author_nickname", "auction_max_price"]:
            if representation.get(field) is None:
                representation.pop(field)

        return representation


class BaseBidSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=False,
    )
    auction_name = serializers.CharField(source="auction.auction_name", read_only=True)
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    is_top_bid = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = [
            "id",
            "author",
            "author_name",
            "author_nickname",
            "author_avatar",
            "author_kyc_verified",
            "auction",
            "auction_name",
            "offer",
            "description",
            "delivery_fee",
            "status",
            "images",
            "is_top_bid",
        ]
        read_only_fields = [
            "id",
            "status",
            "author",
            "author_name",
            "author_nickname",
            "author_avatar",
            "author_kyc_verified",
            "auction",
            "auction_name",
            "is_top_bid",
        ]

    def get_auction_statistics(self, auction):
        """Get or initialize auction statistics"""
        auction_statistics = AuctionStatistics.objects.filter(auction=auction).first()
        if auction_statistics:
            self.context["previous_top_bid"] = (
                auction_statistics.top_bid_object.offer
                if auction_statistics.top_bid_object
                else None
            )
            self.context["previous_top_bid_object"] = (
                auction_statistics.top_bid_object.id
                if auction_statistics.top_bid_object
                else None
            )

        return auction_statistics

    def get_is_top_bid(self, current_bid):
        """Check if current bid is the top bid for the auction"""

        # Get latest auction statistics
        if "previous_top_bid" not in self.context:
            self.get_auction_statistics(current_bid.auction)

        previous_top_bid = self.context.get("previous_top_bid")
        previous_top_bid_object = self.context.get("previous_top_bid_object")

        if previous_top_bid is None:
            return True
        if str(current_bid.id) == str(previous_top_bid_object):
            return True
        if current_bid.offer < previous_top_bid:
            return True

        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        currency = instance.auction.currency
        offer = representation["offer"]
        representation["offer"] = f"{get_currency_symbol(currency)}{offer}"

        delivery_fee = representation.get("delivery_fee")
        if delivery_fee:
            representation["delivery_fee"] = (
                f"{get_currency_symbol(currency)}{delivery_fee}"
            )

        representation["images"] = [
            image.image_url.url for image in instance.images.all()
        ]

        return representation


class CreateBidSerializer(BaseBidSerializer):

    def validate(self, attrs):
        """
        Validate the bid data.
        """
        validated_data = super().validate(attrs)

        # Validate image count
        images = validated_data.get("images", [])
        if len(images) > 5:
            raise PermissionDenied(
                _("As a non-premium user you cannot upload more than 5 images per bid.")
            )

        return validated_data

    def update_auction_statistics(self, bid):
        """Update auction statistics with new bid information"""

        auction_statistics = self.get_auction_statistics(bid.auction)

        if not auction_statistics:
            return None

        with transaction.atomic():
            # Update bid count
            auction_statistics.total_bids_count = F("total_bids_count") + 1

            # Update top bid
            if (
                not auction_statistics.top_bid_object
                or bid.offer < auction_statistics.top_bid_object.offer
            ):
                auction_statistics.top_bid = bid.offer
                auction_statistics.top_bid_author = bid.author
                auction_statistics.top_bid_object = bid

            auction_statistics.save()
            auction_statistics.refresh_from_db()

        return auction_statistics

    def create(self, validated_data):
        image_data = validated_data.pop("images", [])
        user = self.context["request"].user
        validated_data["author"] = user.id

        try:
            with transaction.atomic():
                # Create bid
                bid = Bid.objects.create(**validated_data)

                # Bulk create images if any
                if image_data:
                    bid_images = [
                        BidImage(
                            bid=bid,
                            image_url=image_array,
                        )
                        for index, image_array in enumerate(image_data, start=1)
                    ]
                    BidImage.objects.bulk_create(bid_images)

                # Update statistics
                auction_statistics = self.update_auction_statistics(bid)
                if not auction_statistics:
                    raise serializers.ValidationError(
                        "Failed to update auction statistics."
                    )

                # Refresh bid to get latest data
                bid.refresh_from_db()

                return bid

        except IntegrityError as e:
            raise serializers.ValidationError(f"Failed to create bid: {str(e)}")
        except Exception as e:
            raise serializers.ValidationError(f"An unexpected error occurred: {str(e)}")


class UpdateBidSerializer(BaseBidSerializer):
    class Meta(BaseBidSerializer.Meta):
        read_only_fields = [
            "id",
            "author",
            "author_name",
            "author_nickname",
            "author_avatar",
            "author_kyc_verified",
            "auction",
            "auction_name",
            "description",
            "delivery_fee",
            "status",
            "images",
            "is_top_bid",
        ]

    def update(self, instance, validated_data):
        auction_statistics = self.get_auction_statistics(instance.auction)
        new_offer = validated_data.get("offer")
        current_offer = instance.offer
        self.validate_bid_offer(new_offer, current_offer)
        bid = super().update(instance, validated_data)

        # get and update auction stat
        if (
            not auction_statistics.top_bid_object
            or bid.offer < auction_statistics.top_bid_object.offer
        ):
            auction_statistics.top_bid = bid.offer
            auction_statistics.top_bid_author = bid.author
            auction_statistics.top_bid_object = bid
            auction_statistics.save()

        return bid

    def validate_bid_offer(self, new_offer, current_offer):
        if current_offer <= new_offer:
            raise serializers.ValidationError(
                _(
                    "You can not update bid with "
                    "an offer that is more or equal than the "
                    "current one. You can only lower "
                    "the offer when updating a bid"
                )
            )


class SellerStatisticsSerializer(serializers.Serializer):
    total_bids = serializers.IntegerField()
    total_auctions_participated = serializers.IntegerField()
    completed_auctions_participated = serializers.IntegerField()
    auctions_won = serializers.IntegerField()
    live_auction_bids = serializers.IntegerField()
    success_rate = serializers.FloatField()
