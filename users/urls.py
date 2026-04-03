from django.urls import path, include
from . import views

app_name = 'users'

urlpatterns = [
   
    path('', include('django.contrib.auth.urls')),
    
    # register
    
    path('register/', views.register, name='register'),
    path('logout/', views.log_out, name="logout"),

    path('redirect/', views.role_redirect, name='role_redirect'),
    path('customer/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/warranty/', views.customer_warranty, name='customer_warranty'),
    
    path('customer/claims/', views.customer_claims, name='customer_claims'),
    path('customer/inspection/', views.customer_inspection, name='customer_inspection'),
]