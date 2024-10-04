from django_filters import rest_framework as filters

from auction.models.auction import (
    AcceptedBiddersChoices,
    Auction,
    ConditionChoices,
    CurrencyChoices,
    StatusChoices,
)
from auction.models.bookmark import Bookmark
from auction.models.category import CategoryChoices


class AuctionFilterSet(filters.FilterSet):
    status = filters.ChoiceFilter(choices=StatusChoices.choices, field_name="status")

    class Meta:
        model = Auction
        fields = [
            "status",
        ]


class BookmarkFilterSet(filters.FilterSet):
    status = filters.ChoiceFilter(
        choices=StatusChoices.choices, field_name="auction__status"
    )

    condition = filters.ChoiceFilter(
        choices=ConditionChoices.choices, field_name="auction__condition"
    )

    accepted_bidders = filters.ChoiceFilter(
        choices=AcceptedBiddersChoices.choices, field_name="auction__accepted_bidders"
    )

    accepted_locations = filters.CharFilter(field_name="auction__accepted_locations")

    currency = filters.ChoiceFilter(
        choices=CurrencyChoices.choices, field_name="auction__currency"
    )

    max_price = filters.NumberFilter(field_name="auction__max_price", lookup_expr="lte")

    min_price = filters.NumberFilter(field_name="auction__max_price", lookup_expr="gte")
    start_date = filters.DateFilter(field_name="auction__start_date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="auction__end_date", lookup_expr="lte")
    category = filters.ChoiceFilter(
        choices=CategoryChoices.choices, field_name="auction__category__name"
    )

    class Meta:
        model = Bookmark
        fields = [
            "status",
            "condition",
            "accepted_bidders",
            "accepted_locations",
            "currency",
            "max_price",
            "min_price",
        ]
