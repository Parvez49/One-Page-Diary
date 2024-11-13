
## select_related
 is a QuerySet method that performs a SQL join and includes the fields of related models in the same query for fetching a list of objects and need to access their related foreign keys or one-to-one relationships. <br>
 <b>Join then Query: </b> performs an SQL JOIN between the main model and the related model(s) in a single query.

 Ex: Order.objects.select_related('created_by')

```
 SELECT 
    "order"."id", 
    "order"."title", 
    "user"."id" AS "created_by_id", 
    "user"."name" AS "created_by_name" 
 FROM 
    "order"
 INNER JOIN 
    "user" ON ("order"."created_by" = "user"."id")

```


## prefetch_related
 Used for ManyToMany relationships or when need to query multiple tables independently and then combine the results.
 <b>Query then Join: </b> runs separate queries for each of the related models, then it joins the results in Python.

 Example 1:
 ```

   class Author(models.Model):
    name = models.CharField(max_length=100)

   class Genre(models.Model):
    name = models.CharField(max_length=100)

   class Book(models.Model):
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
   
   books = Book.objects.prefetch_related(
    Prefetch('authors', queryset=Author.objects.filter(name__startswith='J')),
    'publisher'
   ).all()

   The above take 2 query.
 ```

 Example 2:
 ```
   class LabelRefConfiguration(BaseModelWithUID):
    label_ref = models.CharField(max_length=100,unique=True)

   class Order(BaseModelWithUID):
    job_bag_number = models.CharField(max_length=150, blank=True)

   class  OrderProductCodeConnector(BaseModelWithUID):
    order = models.ForeignKey(Order, related_name='product_code_orders', on_delete=models.SET_NULL, null=True, blank=True)
    product_code = models.ForeignKey(LabelRefConfiguration, related_name='product_code_details', on_delete=models.SET_NULL, null=True, blank=True)


    queryset = Order.objects.prefetch_related(
                Prefetch('product_code_orders',
                         queryset=OrderProductCodeConnector.objects.select_related('product_code'))
            ).all()

    # we get order info with LabeRefConfiguration.
 ```

 Example 3 (Very Complex):
 ```
    class LabelRefConfiguration(BaseModelWithUID):
        label_ref = models.CharField(max_length=100,unique=True)

    class Order(BaseModelWithUID):
        job_bag_number = models.CharField(max_length=150, blank=True)

    class  OrderProductCodeConnector(BaseModelWithUID):
        order = models.ForeignKey(Order, related_name='product_code_orders', on_delete=models.SET_NULL, null=True, blank=True)
        product_code = models.ForeignKey(LabelRefConfiguration, related_name='product_code_details', on_delete=models.SET_NULL, null=True, blank=True)

    class Production(BaseModelWithUID):
        order = models.ForeignKey(Order, related_name='productions',on_delete=models.SET_NULL,null=True,blank=True)

    class QC(BaseModelWithUID):
        production_details = models.ForeignKey(Production, related_name='qc', on_delete=models.SET_NULL, blank=True, null=True)

    class Challan(BaseModelWithUID):
        invoice_number = models.CharField(max_length=50,null=True,blank=True)

    class GatePassOrder(BaseModelWithUID):
        gate_pass_number = models.CharField(max_length=50, null=True, blank=True)

    class ChallanGatePassOrderConnector(BaseModelWithUID):
        gate_pass = models.ForeignKey(GatePassOrder, related_name='gate_pass', on_delete=models.SET_NULL, null=True)
        challan = models.ForeignKey(Challan, related_name='challan_gate_pass',on_delete=models.SET_NULL, null=True)

    
    queryset = GatePassOrder.objects.prefetch_related(
                    Prefetch(
                        'gate_pass',
                        queryset=ChallanGatePassOrderConnector.objects.select_related(
                            'challan',
                            'challan__qc_details',
                            'challan__qc_details__production_details',
                            'challan__qc_details__production_details__order'
                        ).prefetch_related(
                            Prefetch(
                                'challan__qc_details__production_details__order__product_code_orders',
                                queryset=OrderProductCodeConnector.objects.select_related('product_code')
                            )
                        )
                    )
                ).all()

 ```