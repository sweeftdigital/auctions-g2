from django.db import IntegrityError, transaction
from django.db.models import F
from rest_framework import serializers

from auction.models.auction import AuctionStatistics
from auction.utils import get_currency_symbol
from bid.models.bid import Bid, BidImage, StatusChoices


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
            "auction",
            "offer",
            "description",
            "delivery_fee",
            "status",
            "images",
        ]


class BaseBidSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=False,
    )
    bid_images = serializers.SerializerMethodField(read_only=True)
    auction_name = serializers.CharField(source="auction.auction_name", read_only=True)
    author_name = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = Bid
        fields = [
            "id",
            "author",
            "author_name",
            "auction",
            "auction_name",
            "offer",
            "description",
            "delivery_fee",
            "status",
            "images",
            "bid_images",
        ]
        read_only_fields = [
            "id",
            "status",
            "author",
            "author_name",
            "auction",
            "auction_name",
            "bid_images",
        ]

    def get_bid_images(self, obj):
        """Return all image URLs for this bid"""
        # Using the correct related_name from your model: 'images'
        return [image.image_url.url for image in obj.images.all()]

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

        return representation


class CreateBidSerializer(BaseBidSerializer):
    def create(self, validated_data):
        image_data = validated_data.pop("images", [])
        user = self.context["request"].user
        validated_data["author"] = user.id

        try:
            with transaction.atomic():  # Start the transaction
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

                # Refresh to get the latest data including images
                bid.refresh_from_db()

                return bid

        except IntegrityError:
            raise serializers.ValidationError(
                "Failed to create bid. Please check your input."
            )
        except Exception as e:
            raise serializers.ValidationError(f"An unexpected error occurred: {str(e)}")


class UpdateBidSerializer(BaseBidSerializer):
    class Meta(BaseBidSerializer.Meta):
        fields = ["offer"]

    def update(self, instance, validated_data):
        status = instance.status

        if status == StatusChoices.REJECTED:
            raise serializers.ValidationError("Rejected bids cannot be updated.")

        if status == StatusChoices.APPROVED and validated_data["offer"] >= instance.offer:
            raise serializers.ValidationError(
                "For approved bids, the offer can only be reduced."
            )

        instance.offer = validated_data["offer"]
        instance.save()
        return instance
