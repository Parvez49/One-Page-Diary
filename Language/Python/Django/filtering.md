### Basic Filtering

```
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ]
}

class PermissionViewSet(ModelViewSet):
    serializer_class = PermissionListSerializer
    queryset = Permission.objects.all()
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['created_at', 'name']
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

filter_backends in view is not necessary if filter set in settings.py. 
```

### Customizable Filtering
```
from typing import Protocol, TypeVar
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters


T = TypeVar('T', bound='SupportsMineFilter')

class SupportsMineFilter(Protocol):
    request: HttpRequest  # Ensures `request` attribute exists
    form: Form  # Ensures `form` attribute with `cleaned_data` exists

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        ...  # Ensures `filter_queryset` method exists

class MineFilterMixin:
    def filter_queryset(self: T, queryset):
        # customize queryset before filtering
        return super(MineFilterMixin, self).filter_queryset(queryset)

    def filter_mine(self: T, queryset, field_name, value):
        return (
            queryset.filter(created_by_id=self.request.user.id)
            if value and self.request.user.is_authenticated
            else queryset
        )

class CustomFilter(MineFilterMixin, filters.FilterSet):
    """Filter class for the model."""

    date = filters.CharFilter(label=_('Date'), method="filter_date")
    exclude_ids = NumberInFilter(label=_('Exclude IDs'), field_name='id', exclude=True)
    mine = filters.BooleanFilter(label=_('Mine'), method='filter_mine')

    class Meta:
        model = Model
        fields = [
            'date',
            'exclude_ids',
            'mine',
        ]

    def filter_date(self, queryset, name, value):
        if value.lower() == "null":
            return queryset.filter(date__isnull=True)
        return queryset.filter(date=value)
