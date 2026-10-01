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
    path('expenses/<int:pk>/', views.expense_detail, name='expense_detail'),
    path('expenses/<int:pk>/approve/', views.approve_expense, name='approve_expense'),
    path('expenses/<int:pk>/reject/', views.reject_expense, name='reject_expense'),
    path('vouchers/<int:pk>/', views.voucher_detail, name='voucher_detail'),
    path('ledger/', views.ledger, name='ledger'),
    path('reconciliation/', views.reconciliation, name='reconciliation'),
]
