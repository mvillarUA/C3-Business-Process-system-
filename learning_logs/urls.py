from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
app_name = 'learning_logs'
urlpatterns = [
# Home page
    path('', views.index, name='index'),
    path('topics/', views.topics, name='topics'),
    path('topics/<int:topic_id>', views.topic, name='topic'),
    path('new_topic/', views.new_topic, name='new_topic'),
    path('new_entry/<int:topic_id>',views.new_entry, name='new_entry'),
    path('edit_entry/<int:entry_id>/', views.edit_entry, name='edit_entry'),
    path("claims/", views.claims, name="claims"),
    path('sales/', views.sales, name='sales'),
    path('sales/list/', views.view_sales, name='view_sales'),
    path('sales/new/', views.new_sale, name='new_sale'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/new/', views.new_inventory, name='new_inventory'),
    path("claims/", views.claims, name="claims"),
    path('claims/new/', views.new_claim, name='new_claim'),
    path("sales/", views.sales, name="sales"),
    path("inventory/", views.inventory, name="inventory"),
    path('claims/<int:claim_id>/', views.claim_detail, name='claim_detail'),
    path('claims/<int:claim_id>/update/<str:status>/', views.update_claim_status, name='update_claim_status'),
    path('claims/upload/', views.upload_documents, name='upload_documents'),
    path('claims/review/', views.review_claim, name='review_claim'),
    path('claims/submit/', views.submit_claim, name='submit_claim'),
    path('claims/<int:claim_id>/delete/', views.delete_claim, name='delete_claim')
]