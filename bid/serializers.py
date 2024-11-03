from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

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

    class Meta:
        model = Bid
        fields = [
            "id",
            "author",
            "author_nickname",
            "author_avatar",
            "author_kyc_verified",
            "auction",
            "offer",
            "description",
            "delivery_fee",
            "status",
            "images",
        ]

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

    def create_bid_images(self, bid, image_data):
        """Create images for the bid"""

        for index, image_array in enumerate(image_data, start=1):
            image_name = f"{bid.id}-image_{index}"
            image_array.name = image_name
            BidImage.objects.create(bid=bid, image_url=image_array)

    def create(self, validated_data):
        image_data = validated_data.pop("images", [])
        user = self.context["request"].user
        validated_data["author"] = user.id

        try:
            with transaction.atomic():
                # Create bid
                bid = Bid.objects.create(**validated_data)

                # Create images
                if image_data:
                    self.create_bid_images(bid, image_data)

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
