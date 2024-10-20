from rest_framework import serializers

from auction.models.auction import AcceptedBiddersChoices
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
            "auction",
            "auction_name",
        ]

    def validate(self, data):
        auction = self.context.get("auction")
        user = self.context["request"].user

        if auction is None:
            raise serializers.ValidationError("Auction does not exist.")

        if auction.status != "Live":
            raise serializers.ValidationError("You can only bid on live auctions.")

        if not user.is_seller:
            raise serializers.ValidationError("Only sellers can place bids.")

        if (
            auction.accepted_bidders == AcceptedBiddersChoices.COMPANY
            and not user.is_company()
        ):
            raise serializers.ValidationError("Only companies can bid on this auction.")
        if (
            auction.accepted_bidders == AcceptedBiddersChoices.INDIVIDUAL
            and not user.is_individual()
        ):
            raise serializers.ValidationError("Only individuals can bid on this auction.")
        if auction.accepted_bidders == AcceptedBiddersChoices.BOTH and not (
            user.is_company() or user.is_individual()
        ):
            raise serializers.ValidationError(
                "Only individuals or companies can bid on this auction."
            )

        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Attach currency symbol to offer and delivery_fee fields
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

        bid = Bid.objects.create(**validated_data)

        for index, image_array in enumerate(image_data, start=1):
            image_file = image_array
            image_name = f"{bid.id}-image_{index}"
            image_file.name = image_name
            BidImage.objects.create(bid=bid, image_url=image_file)

        return bid


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
