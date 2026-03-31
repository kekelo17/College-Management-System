from django.contrib import admin
from .models import (
    FeeCategory, FeeStructure, Invoice, InvoiceItem, Payment,
    PaymentReceipt, FeeDiscount, StudentDiscount, Expense
)


@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'is_mandatory']
    list_filter = ['is_active', 'is_mandatory']
    search_fields = ['name', 'code']


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['category', 'department', 'amount', 'frequency', 'is_mandatory', 'is_active']
    list_filter = ['category', 'is_active', 'is_mandatory', 'frequency', 'department']
    search_fields = ['category__name', 'category__code']
    readonly_fields = ['created_at', 'updated_at']


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'student', 'semester', 'total_amount', 
                   'amount_paid', 'balance', 'status', 'issue_date']
    list_filter = ['status', 'semester', 'issue_date']
    search_fields = ['invoice_number', 'student__first_name', 'student__last_name', 
                   'student__student_id']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at', 'total_amount', 'balance']
    inlines = [InvoiceItemInline]


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'amount']
    search_fields = ['invoice__invoice_number', 'description']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'invoice', 'student', 'amount', 'payment_method', 
                   'status', 'payment_date']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['payment_number', 'transaction_id', 'student__first_name', 
                   'student__last_name', 'student__student_id']
    readonly_fields = ['payment_number', 'created_at', 'updated_at']


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'student', 'amount', 'issued_at', 'is_cancelled']
    list_filter = ['is_cancelled', 'issued_at']
    search_fields = ['receipt_number', 'student__first_name', 'student__last_name']


@admin.register(FeeDiscount)
class FeeDiscountAdmin(admin.ModelAdmin):
    list_display = ['discount_code', 'name', 'discount_type', 'value', 'is_active', 'valid_from']
    list_filter = ['is_active', 'discount_type', 'is_scholarship', 'valid_from']
    search_fields = ['discount_code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudentDiscount)
class StudentDiscountAdmin(admin.ModelAdmin):
    list_display = ['student', 'discount', 'semester', 'amount', 'is_approved']
    list_filter = ['is_approved', 'discount__discount_type']
    search_fields = ['student__first_name', 'student__last_name', 'discount__name']
    readonly_fields = ['created_at']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_number', 'category', 'description', 'amount', 
                   'expense_date', 'is_approved']
    list_filter = ['category', 'is_approved', 'expense_date']
    search_fields = ['expense_number', 'description', 'vendor']
    readonly_fields = ['expense_number', 'created_at', 'updated_at']
