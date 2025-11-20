from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('add/', views.add_expense, name='add_expense'),
    path('delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('budget/', views.manage_budget, name='manage_budget'),
    path('close-modal/', views.close_modal, name='close_modal'),
]