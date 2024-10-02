from django_filters import rest_framework as filters

from auction.models.auction import (
    AcceptedBiddersChoices,
    Auction,
    ConditionChoices,
    CurrencyChoices,
    StatusChoices,
)
from auction.models.category import CategoryChoices


class AuctionFilterSet(filters.FilterSet):
    status = filters.ChoiceFilter(choices=StatusChoices.choices, field_name="status")

    condition = filters.ChoiceFilter(
        choices=ConditionChoices.choices, field_name="condition"
    )

    accepted_bidders = filters.ChoiceFilter(
        choices=AcceptedBiddersChoices.choices, field_name="accepted_bidders"
    )

    accepted_locations = filters.CharFilter(field_name="accepted_locations")

    currency = filters.ChoiceFilter(
        choices=CurrencyChoices.choices, field_name="currency"
    )
    max_price = filters.NumberFilter(field_name="max_price", lookup_expr="lte")
    min_price = filters.NumberFilter(field_name="max_price", lookup_expr="gte")
    start_date = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="end_date", lookup_expr="lte")
    # category = filters.ModelChoiceFilter(queryset=Category.objects.all(), field_name="category__name")
    category = filters.ChoiceFilter(
        choices=CategoryChoices.choices, field_name="category__name"
    )

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
            "category",
        ]
