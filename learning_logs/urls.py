from django.urls import path
from . import views
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

]