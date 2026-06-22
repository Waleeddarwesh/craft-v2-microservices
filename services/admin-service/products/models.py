from django.db import models
from accounts.models import Supplier
from django.utils.text import slugify
from accounts .models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.db.models import Avg
from django.utils.timezone import now
from Handcrafts.utils.translation import translate_text

class Category(models.Model):
    CategoryID = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=100)
    Description = models.TextField()
    Picture = models.ImageField(upload_to='category_images/%y/%m/%d', blank=True, null=True)
    Active = models.BooleanField(default=True)
    Slug = models.SlugField(null=True,blank=True, unique=True)

    def __str__(self):
        return self.Title
    
class MatCategory(models.Model):
    MatID = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=100)
    Picture = models.ImageField(upload_to='category_images/%y/%m/%d', blank=True, null=True)
    Active = models.BooleanField(default=True)
    Slug = models.SlugField(null=True,blank=True, unique=True)

    def __str__(self):
        return self.Title
    
class Product(models.Model):
    class PublishStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    id = models.AutoField(primary_key=True)
    ProductName = models.CharField(max_length=100)
    ProductDescription = models.TextField()
    MatCategory = models.ForeignKey(MatCategory, on_delete=models.CASCADE,blank=True, null=True,related_name = "MatCatPro")
    Category = models.ForeignKey(Category, on_delete=models.CASCADE,blank=True, null=True,related_name = "CatPro")
    Supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, db_column='supplier_id')
    QuantityPerUnit = models.CharField(max_length=50)
    UnitPrice = models.DecimalField(max_digits=10, decimal_places=2)
    UnitWeight = models.DecimalField(max_digits=5, decimal_places=2)
    Stock = models.IntegerField(null=False,blank=False)
    OutOfStock = models.BooleanField(default=False)
    DiscountAvailable = models.BooleanField(default=False)
    Discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    DiscountPercentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    Rating = models.DecimalField(max_digits=10, decimal_places=2,default= 5.0,validators=(MinValueValidator(0.0), MaxValueValidator(5.0)))
    Publish_Date = models.DateTimeField(auto_now_add=True)
    publish_status = models.CharField(max_length=20, choices=PublishStatus.choices, default=PublishStatus.APPROVED) # Defaulting to approved to prevent breaking existing 
    width = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True,validators=(MinValueValidator(0.0), MaxValueValidator(1000.0)))
    height = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True,validators=(MinValueValidator(0.0), MaxValueValidator(1000.0)))
    watt = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True,validators=(MinValueValidator(0.0), MaxValueValidator(1000.0)))
    rejection_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['ProductName', 'ProductDescription'], name='prod_name_desc_idx'),
            models.Index(fields=['UnitPrice'], name='prod_price_idx'),
            models.Index(fields=['Rating'], name='prod_rating_idx'),
        ]
        
    def __str__(self):
        return self.ProductName

    def update_rating(self):
        avg_rating = self.product_rating.aggregate(Avg('rating'))['rating__avg']
        self.Rating = avg_rating if avg_rating is not None else 0
        self.save()

    def save(self, *args, **kwargs):
        if self.DiscountPercentage > 0:
            self.Discount = (self.UnitPrice * self.DiscountPercentage) / 100
            self.UnitPrice = (self.UnitPrice - self.Discount)

        else:
            self.Discount = 0.0
        super().save(*args, **kwargs)
        
@receiver(pre_save, sender=Product)
def toggle_out_of_stock(sender, instance, **kwargs):
    if instance.Stock == 0:
        instance.OutOfStock = True
    else:
        instance.OutOfStock = False    
               
class ProImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name = "images")
    image = models.ImageField(upload_to="product_images/%y/%m/%d", default="", null=True, blank=True)
    
    def __str__(self):
        return self.product.ProductName

class ProColors(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name = "Colors")
    Color = models.CharField(max_length=20,blank=True, null=True) 

    def __str__(self):
        return self.product.ProductName
    
class ProSizes(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name = "Sizes")
    Size = models.CharField(max_length=20,blank=True, null=True) 

    def __str__(self):
        return self.product.ProductName

class Posters(models.Model):
    name = models.CharField(max_length=100)
    image_link = models.ImageField(upload_to="posters_images/%y/%m/%d")
    redierct_link = models.CharField(max_length=200,blank=True,null=True)

    def __str__(self):
        return self.name
    
class Collection(models.Model):
    supplier = models.ForeignKey(
        Supplier, 
        related_name='collections', 
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=now, editable=False)

    def __str__(self):
        return self.name

class CollectionItem(models.Model):
    collection = models.ForeignKey(
        Collection, 
        related_name='items', 
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, 
        related_name='collection_items', 
        on_delete=models.CASCADE
    )
    added_at = models.DateTimeField(default=now, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['collection', 'product'], name='unique_collection_item')
        ]

    def __str__(self):
        return f"{self.product.ProductName} in {self.collection.name}"

@receiver(pre_save, sender=Category)
def auto_translate_category(sender, instance, **kwargs):
    if not instance.Title_ar and instance.Title_en:
        instance.Title_ar = translate_text(instance.Title_en, source='en', target='ar')
    elif not instance.Title_en and instance.Title_ar:
        instance.Title_en = translate_text(instance.Title_ar, source='ar', target='en')

    if not instance.Description_ar and instance.Description_en:
        instance.Description_ar = translate_text(instance.Description_en, source='en', target='ar')
    elif not instance.Description_en and instance.Description_ar:
        instance.Description_en = translate_text(instance.Description_ar, source='ar', target='en')

@receiver(pre_save, sender=MatCategory)
def auto_translate_matcategory(sender, instance, **kwargs):
    if not instance.Title_ar and instance.Title_en:
        instance.Title_ar = translate_text(instance.Title_en, source='en', target='ar')
    elif not instance.Title_en and instance.Title_ar:
        instance.Title_en = translate_text(instance.Title_ar, source='ar', target='en')

@receiver(pre_save, sender=Product)
def auto_translate_product_fields(sender, instance, **kwargs):
    if not instance.ProductName_ar and instance.ProductName_en:
        instance.ProductName_ar = translate_text(instance.ProductName_en, source='en', target='ar')
    elif not instance.ProductName_en and instance.ProductName_ar:
        instance.ProductName_en = translate_text(instance.ProductName_ar, source='ar', target='en')

    if not instance.ProductDescription_ar and instance.ProductDescription_en:
        instance.ProductDescription_ar = translate_text(instance.ProductDescription_en, source='en', target='ar')
    elif not instance.ProductDescription_en and instance.ProductDescription_ar:
        instance.ProductDescription_en = translate_text(instance.ProductDescription_ar, source='ar', target='en')

@receiver(pre_save, sender=Collection)
def auto_translate_collection(sender, instance, **kwargs):
    if not instance.name_ar and instance.name_en:
        instance.name_ar = translate_text(instance.name_en, source='en', target='ar')
    elif not instance.name_en and instance.name_ar:
        instance.name_en = translate_text(instance.name_ar, source='ar', target='en')

