from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/new/', views.project_create, name='project_create'),
    path('advances/', views.advance_list, name='advance_list'),
    path('advances/new/', views.advance_create, name='advance_create'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/new/', views.expense_create, name='expense_create'),
    path('reconciliation/', views.reconciliation, name='reconciliation'),
]
