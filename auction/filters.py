from django_filters import rest_framework as filters

from auction.models.auction import (
    AcceptedBiddersChoices,
    AcceptedLocations,
    Auction,
    ConditionChoices,
    CurrencyChoices,
    StatusChoices,
)


class AuctionFilterSet(filters.FilterSet):
    status = filters.ChoiceFilter(choices=StatusChoices.choices, field_name="status")

    condition = filters.ChoiceFilter(
        choices=ConditionChoices.choices, field_name="condition"
    )

    accepted_bidders = filters.ChoiceFilter(
        choices=AcceptedBiddersChoices.choices, field_name="accepted_bidders"
    )

    accepted_locations = filters.ChoiceFilter(
        choices=AcceptedLocations.choices, field_name="accepted_locations"
    )

    currency = filters.ChoiceFilter(
        choices=CurrencyChoices.choices, field_name="currency"
    )

    class Meta:
        model = Auction
        fields = [
            "status",
            "condition",
            "accepted_bidders",
            "accepted_locations",
            "currency",
        ]
