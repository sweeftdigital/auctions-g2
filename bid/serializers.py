from django.db import IntegrityError, transaction
from django.db.models import F
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

        representation["images"] = [
            image.image_url.url for image in instance.images.all()
        ]

        return representation


class CreateBidSerializer(BaseBidSerializer):
    def create(self, validated_data):
        image_data = validated_data.pop("images", [])
        user = self.context["request"].user
        validated_data["author"] = user.id

        try:
            with transaction.atomic():
                bid = Bid.objects.create(**validated_data)

                for index, image_array in enumerate(image_data, start=1):
                    image_file = image_array
                    image_name = f"{bid.id}-image_{index}"
                    image_file.name = image_name
                    BidImage.objects.create(bid=bid, image_url=image_file)

                # Update statistics
                AuctionStatistics.objects.filter(auction=bid.auction).update(
                    total_bids_count=F("total_bids_count") + 1
                )
                self.determine_top_bid(bid)

                # Refresh to get the latest data including images
                bid.refresh_from_db()

                return bid

        except IntegrityError:
            raise serializers.ValidationError(
                "Failed to create bid. Please check your input."
            )
        except Exception as e:
            raise serializers.ValidationError(f"An unexpected error occurred: {str(e)}")

    def determine_top_bid(self, bid):
        auction_statistics = AuctionStatistics.objects.filter(auction=bid.auction).first()
        top_bid = auction_statistics.top_bid
        if top_bid and bid.offer < top_bid:
            auction_statistics.top_bid = bid.offer
            auction_statistics.top_bid_author = bid.author
        elif not top_bid:
            auction_statistics.top_bid = bid.offer
            auction_statistics.top_bid_author = bid.author

        auction_statistics.save()

        return auction_statistics


class UpdateBidSerializer(BaseBidSerializer):
    class Meta(BaseBidSerializer.Meta):
        model = Bid
        fields = ["offer"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        return {
            "offer": representation["offer"],
        }
