from rest_framework import serializers

from auction.models.auction import AcceptedBiddersChoices
from bid.models.bid import Bid, BidImage, StatusChoices


class BidImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidImage
        fields = ["image_url"]


class BidSerializer(serializers.ModelSerializer):
    images = BidImageSerializer(many=True, required=False)
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

    def update(self, instance, validated_data):
        """Handle updates based on the status of the bid"""
        status = instance.status

        if status == StatusChoices.REJECTED:
            raise serializers.ValidationError("Rejected bids cannot be updated.")

        if status == StatusChoices.APPROVED:
            if "offer" in validated_data:
                new_offer = validated_data["offer"]
                if new_offer >= instance.offer:
                    raise serializers.ValidationError(
                        "For approved bids, the offer can only be reduced."
                    )
            else:
                raise serializers.ValidationError(
                    "For approved bids, only the offer can be changed."
                )

        if status == StatusChoices.PENDING:
            return super().update(instance, validated_data)

        return super().update(instance, validated_data)

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])

        user = self.context["request"].user
        validated_data["author"] = user.id

        bid = Bid.objects.create(**validated_data)

        for image_data in images_data:
            BidImage.objects.create(bid=bid, **image_data)

        return bid
