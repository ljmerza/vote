from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_poll, name='create_poll'),
    path('poll/<slug:slug>/', views.vote_page, name='vote_page'),
    path('poll/<slug:slug>/vote/', views.vote, name='vote'),
    path('poll/<slug:slug>/results/', views.public_results, name='public_results'),
    path('results/<uuid:admin_token>/', views.admin_results, name='admin_results'),
    path('edit/<uuid:admin_token>/', views.edit_poll, name='edit_poll'),
    path('delete/<uuid:admin_token>/', views.delete_poll, name='delete_poll'),
]
