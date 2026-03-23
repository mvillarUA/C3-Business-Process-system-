from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Topic(models.Model):
    # A topic the user is learning about
    text = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        # Return a string representation of the model
        return self.text

class Entry(models.Model):
    # Something specific learned about a topic
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name_plural = 'Entries'
    
    def __str__(self):
    # Return a string representation of the model
        return f"{self.text[:50]}..."
    
class Dealership(models.Model):
    dealershipid = models.IntegerField(db_column='dealershipID', primary_key=True)
    address = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    phonenumber = models.TextField(db_column='phoneNumber', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Dealership'

    def __str__(self):
        return self.name or f"Dealership {self.dealershipid}"
    
class Customer(models.Model):
    customerid = models.TextField(db_column='customerID', primary_key=True)
    dealershipid = models.ForeignKey(
        Dealership,
        models.DO_NOTHING,
        db_column='dealershipID',
        blank=True,
        null=True
    )
    firstname = models.TextField(db_column='firstName', blank=True, null=True)
    lastname = models.TextField(db_column='lastName', blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Customer'

    def __str__(self):
        first = self.firstname or ""
        last = self.lastname or ""
        return f"{first} {last}".strip() or str(self.customerid)
    
class Vehicle(models.Model):
    vehicleid = models.IntegerField(db_column='vehicleID', primary_key=True)
    customerid = models.ForeignKey(
        Customer,
        models.DO_NOTHING,
        db_column='customerID',
        blank=True,
        null=True
    )
    model = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    mileage = models.TextField(blank=True, null=True)
    vin = models.IntegerField(db_column='VIN', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Vehicle'

    def __str__(self):
        return f"{self.year} {self.model}"


class Warrantypolicy(models.Model):
    policyid = models.IntegerField(db_column='policyID', primary_key=True)
    vehicleid = models.ForeignKey(
        Vehicle,
        models.DO_NOTHING,
        db_column='vehicleID',
        blank=True,
        null=True
    )
    startdate = models.TextField(db_column='startDate', blank=True, null=True)
    enddate = models.FloatField(db_column='endDate', blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    coveragetype = models.TextField(db_column='coverageType', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'WarrantyPolicy'

class InventoryItem(models.Model):
   item_name = models.CharField(max_length=100)
   sku = models.CharField(max_length=50, unique=True)
   quantity = models.PositiveIntegerField(default=0)
   reorder_level = models.PositiveIntegerField(default=5)
   description = models.TextField(blank=True)
   created_at = models.DateTimeField(auto_now_add=True)


   def stock_status(self):
       if self.quantity == 0:
           return "Out"
       elif self.quantity <= self.reorder_level:
           return "Low"
       return "Available"


   def __str__(self):
       return f"{self.item_name} ({self.sku})"
