from django.contrib import admin

# Register your models here.
from .models import Topic, Entry
from .models import Warrantypolicy, Vehicle, Customer, Dealership


admin.site.register(Topic)
admin.site.register(Entry)


admin.site.register(Warrantypolicy)
admin.site.register(Vehicle)
admin.site.register(Customer)
admin.site.register(Dealership)

