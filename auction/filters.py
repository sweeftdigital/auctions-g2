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
    max_price = filters.NumberFilter(field_name="max_price", lookup_expr="lte")
    min_price = filters.NumberFilter(field_name="max_price", lookup_expr="gte")
    start_date = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="end_date", lookup_expr="lte")

    class Meta:
        model = Auction
        fields = [
            "status",
            "condition",
            "accepted_bidders",
            "accepted_locations",
            "currency",
            "max_price",
            "min_price",
            "start_date",
            "end_date",
        ]
