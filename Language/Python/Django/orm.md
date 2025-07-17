# Django ORM (Object-Relational Mapping) 
 allows to interact with your database using Python code, without writing raw SQL queries.


```
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    product = models.ForeignKey(Product, related_name='orders', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
```

## Basic Queries
```
products = Product.objects.all()     # Getting all objects
product = Product.objects.get(id=1)  # Getting a single object, no object with that ID exists, it will raise a Product.DoesNotExist exception.
products = Product.objects.filter(price__gt=50)   # Products with price greater than 50
                                  description__contains='shirt'         # Contains (substring search)
                                  description__icontains='shirt'        # Case-insensitive contains
                                  name__exact='T-shirt'
                                  name__startswith='T-shirt'
                                  name__endswith='shirt'
                                  price__in=[25, 50, 75]


# exclude() Method: allows to exclude records from a queryset that match a specific set of conditions. This is the opposite of the filter() method.
Model.objects.exclude(field_name__lookup=value)

```

## Aggregation
```
from django.db.models import Sum, Count, Avg, Min, Max

# aggreagate method return {'<key>_<aggregate>':value} , value is None if no data.
total_price = Product.objects.aggregate(Sum('price'))       # Get the total price of all products, return {'price__sum': 12345.67}, {'price__sum': None} not 0 if no products
average_price = Product.objects.aggregate(Avg('price'))     # Get the average price of all products
total_products = Product.objects.aggregate(Count('id'))     # Get the total number of products


# The annotate() method is used to add aggregate values to each object in a QuerySet
products = Product.objects.annotate(order_count=Count('order'))      # products.order_count = 12345, 0 if no order.
products = Product.objects.annotate(order_count=Count('orders', filter=Q(orders__status='completed')))


# alias(*args, **kwargs) Same as annotate(), but instead of annotating objects in the QuerySet, saves the expression for later reuse with other QuerySet methods. 
This is useful when the result of the expression itself is not needed but it is used for filtering, ordering, or as a part of a complex expression.

from django.db.models import Count
>>> blogs = Blog.objects.alias(entries=Count("entry")).filter(entries__gt=5)
```


## Ordering
```
products = Product.objects.all().order_by('price')       # Order products by price in ascending order
products = Product.objects.all().order_by('-price')      # Order products by price in descending order

```

## Inserting Data
```
product = Product(name="T-shirt", description="A cool T-shirt", price=25.99)
product.save()          # Save to the database

Product.objects.create(name="Shirt", description="A red shirt", price=19.99)

Product.objects.bulk_create([
    Product(name="Shirt", description="A red shirt", price=19.99),
    Product(name="Jeans", description="Blue jeans", price=39.99),
])
```

## Updating Data
```
product = Product.objects.get(id=1)
product.price = 29.99
product.save()

Product.objects.filter(price__lt=30).update(price=30.00)
```

## Deleting Data
```
product = Product.objects.get(id=1)
product.delete()

Product.objects.filter(price__lt=30).delete()
```

## Q() Objects
 In Django ORM, Q() objects allow you to create complex queries with AND, OR, and NOT logic. They are essential for building dynamic queries that can't be achieved using the basic filtering methods like filter(), exclude(), or get().

```
from django.db.models import Q

products = Product.objects.filter(Q(price__gt=50) & Q(name__icontains="shirt")) 
products = Product.objects.filter(Q(price__gt=50) | Q(name__icontains="shirt"))
products = Product.objects.filter(~Q(price__gt=50))             # NOT operator (~) for excluding records that meet certain conditions.
products = Product.objects.filter(
    Q(price__gt=50) & (Q(name__icontains="shirt") | Q(description__icontains="cotton"))
)

```

## F()
 The F() expression represents the value of a model field directly in the database. It allows you to perform operations on fields in a query without having to bring the data into Python and then update it.

 Here are some common use cases for F():
 - Field-based Calculations: Perform arithmetic operations between fields of the same model 
 - Comparisons: Compare fields within the same model (e.g., check if one field is greater than another).
 - Updates: Perform updates based on a comparison of model fields (e.g., increment one field based on another's value).
```
from django.db.models import F, Subquery, OuterRef

Model.objects.filter(field_name=F('other_field'))


Product.objects.update(price=F('price') - F('discount'))     # Update the price to be price - discount for each product
products = Product.objects.filter(price__gt=F('discount'))   # Get all products where the price is greater than the discount
Product.objects.filter(stock__gt=10).update(stock=F('stock') + 5)


Product.objects.filter(id=OuterRef('id')).update(
    price=Subquery(Product.objects.filter(category=OuterRef('category')).values('price').annotate(avg_price=Avg('price')).values('avg_price'))
)
# OuterRef('field_name') is used to reference fields from the outer query in a subquery.

```

# ManyToMany Relationship:
ManyToManyField is used when multiple records in one model can relate to multiple records in another.
```
class Media(models.Model):
    title = models.CharField(max_length=200)
    phash = models.CharField(max_length=64, null=True, blank=True)

class Incident(models.Model):
    media = models.ManyToManyField(Media, related_name='incidents')
```
Django creates a hidden intermediary table to manage the relationship.
  - Forward Access (default):
    - incident = Incident.objects.get(id=1)
    - incident.media.all()  # Get all media linked to this incident
  - Reverse Access (using related_name):
    - media = Media.objects.get(id=1)
    - media.incidents.all()  # Get all incidents linked to this media
  -  Filtering Queries:
    - Incident.objects.filter(media__phash__isnull=False)
    - Media.objects.filter(incidents__date__year=2024)
  - Using the through Table:
    - Use .through to access the intermediary table. Enables fine-grained control and filtering on join-level data.
    - Incident.media.through.objects.filter(media__phash__isnull=False)
  - Blocking Reverse Access
    - media = models.ManyToManyField(Media, related_name='+')
    - related_name='+' disables reverse access (media.incident_set won’t work).
    - Still allows .through queries.

## Database Transactions
 Atomic Transactions: Use django.db.transaction.atomic to manage database transactions. This ensures that either all or none of the changes in a block of code are committed to the database.

 ```
    from django.db import transaction
    
    try:
        with transaction.atomic():
            author = Author.objects.create(name="Author Name")
            publisher = Publisher.objects.create(name="Publisher Name")

    except Exception as e:
        # If any exception occurs, all changes will be rolled back
        print(f"Error: {e}")
 ```
 
