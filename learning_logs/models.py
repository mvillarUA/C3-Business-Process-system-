from django.db import models
from django import forms
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
    model = models.TextField(max_length= 100)
    year = models.IntegerField(blank=True, null=True)
    mileage = models.IntegerField(blank=True, null=True)
    vin = models.CharField(max_length= 50,db_column='VIN', blank=True, null=True)

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
    startdate = models.DateField(db_column='startDate', blank=True, null=True)
    enddate = models.DateField(db_column='endDate', blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    coveragetype = models.TextField(db_column='coverageType', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'WarrantyPolicy'
        

class Inventory(models.Model):
    partid = models.IntegerField(db_column='partID', primary_key=True)
    partname = models.TextField(db_column='partName', blank=True, null=True)
    quantity = models.FloatField(blank=True, null=True)
    cost = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Inventory'

    def stock_status(self):
        qty = self.quantity or 0
        if qty == 0:
            return "Out"
        elif qty <= 5:
            return "Low"
        return "Available"

    def __str__(self):
        return self.partname or f"Part {self.partid}"
    
class Claim(models.Model):
    POLICY_LEVEL_CHOICES = [
        ('LOW', 'Under 1500'),
        ('HIGH', '1500+'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('MORE_INFO', 'More Info Required'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2)
    claim_level = models.CharField(max_length=10, choices=POLICY_LEVEL_CHOICES, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    date_created = models.DateTimeField(auto_now_add=True)
    policy_number = models.CharField(max_length=100, default='')
    vin = models.CharField(max_length=100, default='')
    attachment = models.FileField(upload_to='claims/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # AUTO CLASSIFY CLAIM LEVEL
        if self.claim_amount < 1500:
            self.claim_level = 'LOW'
        else:
            self.claim_level = 'HIGH'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ['policy_number', 'vin', 'title', 'description', 'claim_amount']

    def new_claim(request):
        if request.method != 'POST':
            form = ClaimForm()
        else:
            form = ClaimForm(data=request.POST)
            if form.is_valid():
                form.save
                return redirect('learning_logs:claims')
        
        return render(request, 'learning_logs/new_claims.html', {'form': form})
    
    inspection_status = models.CharField(
    max_length=20,
    choices=[
        ('SCHEDULED','Scheduled'),
        ('COMPLETED','Completed'),
        ('EXPIRED','Expired')
    ],
    default='SCHEDULED'
)