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


