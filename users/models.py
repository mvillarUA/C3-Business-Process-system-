from django.db import models
from django.contrib.auth.models import User
from learning_logs.models import Customer

class Profile(models.Model):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('employee', 'Employee'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    

class CustomerAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} -> {self.customer.customerid}"