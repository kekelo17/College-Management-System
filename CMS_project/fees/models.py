from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class FeeCategory(models.Model):
    """Model for fee categories"""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Fee Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class FeeStructure(models.Model):
    """Model for fee structures"""
    FREQUENCY_CHOICES = [
        ('once', 'One Time'),
        ('per_semester', 'Per Semester'),
        ('per_year', 'Per Year'),
        ('monthly', 'Monthly'),
    ]

    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name='structures')
    department = models.ForeignKey('courses.Department', on_delete=models.CASCADE, related_name='fee_structures', null=True, blank=True)
    level = models.CharField(max_length=10, blank=True)  # For specific levels
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='fee_structures', null=True, blank=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='per_semester')
    
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    late_fee_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.category.name} - {self.amount}"

    def clean(self):
        if self.late_fee and self.late_fee_per_day:
            raise ValidationError('Cannot have both flat late fee and per-day late fee')


class Invoice(models.Model):
    """Model for student invoices"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='invoices')
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='invoices')
    
    issue_date = models.DateField()
    due_date = models.DateField()
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    late_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return f"{self.invoice_number} - {self.student}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            self.invoice_number = f"INV-{date_str}-{self.student.student_id}"
            while Invoice.objects.filter(invoice_number=self.invoice_number).exists():
                import uuid
                self.invoice_number = f"INV-{date_str}-{self.student.student_id}-{uuid.uuid4().hex[:4].upper()}"
        
        self.total_amount = self.subtotal - self.discount + self.late_fee
        self.balance = self.total_amount - self.amount_paid
        
        if self.balance == 0:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        
        super().save(*args, **kwargs)


class InvoiceItem(models.Model):
    """Model for invoice line items"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.SET_NULL, null=True, blank=True)
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.CharField(max_length=500)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.invoice} - {self.description}"

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Model for payments"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('pos', 'POS'),
        ('online', 'Online Payment'),
        ('cheque', 'Cheque'),
        ('demand_draft', 'Demand Draft'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    payment_number = models.CharField(max_length=50, unique=True, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Payment details
    transaction_id = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    cheque_number = models.CharField(max_length=50, blank=True)
    
    payment_date = models.DateTimeField()
    received_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, related_name='received_payments')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payment_number} - {self.student} - {self.amount}"

    def save(self, *args, **kwargs):
        if not self.payment_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d%H%M')
            self.payment_number = f"PAY-{date_str}"
            while Payment.objects.filter(payment_number=self.payment_number).exists():
                import uuid
                self.payment_number = f"PAY-{date_str}-{uuid.uuid4().hex[:4].upper()}"
        
        super().save(*args, **kwargs)


class PaymentReceipt(models.Model):
    """Model for payment receipts"""
    receipt_number = models.CharField(max_length=50, unique=True)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='receipts')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_words = models.CharField(max_length=500)
    
    issued_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, related_name='issued_receipts')
    issued_at = models.DateTimeField(auto_now_add=True)
    
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f"{self.receipt_number}"


class FeeDiscount(models.Model):
    """Model for fee discounts/scholarships"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    discount_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Applicability
    applicable_categories = models.ManyToManyField(FeeCategory, blank=True, related_name='discounts')
    departments = models.ManyToManyField('courses.Department', blank=True, related_name='fee_discounts')
    levels = models.CharField(max_length=100, blank=True)  # Comma-separated levels
    
    # Conditions
    min_gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    is_scholarship = models.BooleanField(default=False)
    
    # Validity
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    max_applications = models.PositiveIntegerField(null=True, blank=True)
    applications_used = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.discount_code} - {self.name}"


class StudentDiscount(models.Model):
    """Model for student-specific discounts"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='discounts')
    discount = models.ForeignKey(FeeDiscount, on_delete=models.CASCADE, related_name='student_discounts')
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='student_discounts')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'discount', 'semester']

    def __str__(self):
        return f"{self.student} - {self.discount.name}"


class Expense(models.Model):
    """Model for institutional expenses"""
    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('utilities', 'Utilities'),
        ('maintenance', 'Maintenance'),
        ('supplies', 'Supplies'),
        ('equipment', 'Equipment'),
        ('events', 'Events'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]

    expense_number = models.CharField(max_length=50, unique=True, editable=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    
    vendor = models.CharField(max_length=200, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    receipt = models.FileField(upload_to='fees/expenses/', blank=True, null=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.expense_number} - {self.category} - {self.amount}"

    def save(self, *args, **kwargs):
        if not self.expense_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            self.expense_number = f"EXP-{date_str}-{uuid.uuid4().hex[:4].upper()}"
        super().save(*args, **kwargs)
