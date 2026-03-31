from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    # Fee Category
    path('category/', views.category_list, name='category_list'),
    path('category/create/', views.category_create, name='category_create'),
    path('category/<int:pk>/update/', views.category_update, name='category_update'),
    
    # Fee Structure
    path('structure/', views.structure_list, name='structure_list'),
    path('structure/create/', views.structure_create, name='structure_create'),
    path('structure/<int:pk>/update/', views.structure_update, name='structure_update'),
    
    # Invoice
    path('invoice/', views.invoice_list, name='invoice_list'),
    path('invoice/create/', views.invoice_create, name='invoice_create'),
    path('invoice/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:pk>/update/', views.invoice_update, name='invoice_update'),
    path('invoice/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    
    # Payment
    path('payment/', views.payment_list, name='payment_list'),
    path('payment/create/', views.payment_create, name='payment_create'),
    path('payment/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payment/<int:pk>/verify/', views.payment_verify, name='payment_verify'),
    
    # Student Fees
    path('student/', views.student_fees, name='student_fees'),
    path('student/pay/', views.student_pay, name='student_pay'),
]
