from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('documents/', views.document_list, name='document_list'),
    path('documents/create/', views.document_create, name='document_create'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('api/add-pii-tag/', views.add_pii_tag, name='add_pii_tag'),
    path('register/', views.register, name='register'),
]
