### Django URL Patterns (path)
  - define routes using the path() function:
    ```
      from django.urls import path
      from .views import MyView
    
      app_name = 'v1'
      
      urlpatterns = [
          path('hello/', MyView.as_view(), name='hello'),
      ]
    
      In project-level urls.py:
      path('api/v1/', include('myapp.urls', namespace='v1'))
    ```
    - name='hello' lets reverse this URL later.
    - Usage in template: {% url 'hello' %}
    - Usage in Python: reverse('hello') → returns /hello/
    - reverse('v1:hello')  # with namespace
      
  - DRF ViewSets and Routers
    ```
      from rest_framework.routers import DefaultRouter
      from .views import MyViewSet
      
      router = DefaultRouter()
      router.register(r'data', GraffityViewSet, basename='data')
    ```
    - This generates:
    - data-list	/graffities/	GET, POST
    - data-detail	/graffities/<pk>/	GET, PUT, DELETE
    - Use in reverse: from django.urls import reverse; reverse('v1:graffities-list')
    - Use in template: {% url 'v1:graffities-detail' pk=1 %}


### Django Filter
  - 
