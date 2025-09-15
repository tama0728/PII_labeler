from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('documents/', views.document_list, name='document_list'),
    path('documents/create/', views.document_create, name='document_create'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/download/jsonl/', views.download_jsonl, name='download_jsonl'),
    path('api/add-pii-tag/', views.add_pii_tag, name='add_pii_tag'),
    path('api/delete-pii-tag/', views.delete_pii_tag, name='delete_pii_tag'),
    path('api/update-pii-tag/', views.update_pii_tag, name='update_pii_tag'),
    path('api/delete-document/', views.delete_document, name='delete_document'),
    path('api/bulk-delete-documents/', views.bulk_delete_documents, name='bulk_delete_documents'),
    path('register/', views.register, name='register'),
]
