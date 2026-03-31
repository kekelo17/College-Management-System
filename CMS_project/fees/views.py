from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime

from .models import FeeCategory, FeeStructure, Invoice, InvoiceItem, Payment, PaymentReceipt, FeeDiscount, StudentDiscount
from courses.models import Department
from students.models import Student, Semester
from core.views import log_activity


def is_admin(user):
    return user.is_superuser or user.is_staff


def is_student(user):
    return user.is_authenticated and hasattr(user, 'student')


# Fee Category Views
@login_required
@user_passes_test(is_admin)
def category_list(request):
    """List all fee categories"""
    categories = FeeCategory.objects.all()
    context = {
        'page_title': 'Fee Categories',
        'categories': categories,
    }
    return render(request, 'fees/category_list.html', context)


@login_required
@user_passes_test(is_admin)
def category_create(request):
    """Create a new fee category"""
    if request.method == 'POST':
        try:
            category = FeeCategory(
                name=request.POST.get('name'),
                code=request.POST.get('code'),
                description=request.POST.get('description', ''),
                is_mandatory='is_mandatory' in request.POST,
            )
            category.save()
            
            messages.success(request, f'Fee Category {category.name} created successfully!')
            return redirect('fees:category_list')
        except Exception as e:
            messages.error(request, f'Error creating category: {str(e)}')
    
    context = {'page_title': 'Add Fee Category'}
    return render(request, 'fees/category_form.html', context)


@login_required
@user_passes_test(is_admin)
def category_update(request, pk):
    """Update a fee category"""
    category = get_object_or_404(FeeCategory, pk=pk)
    
    if request.method == 'POST':
        try:
            category.name = request.POST.get('name')
            category.code = request.POST.get('code')
            category.description = request.POST.get('description', '')
            category.is_mandatory = 'is_mandatory' in request.POST
            category.is_active = 'is_active' in request.POST
            category.save()
            
            messages.success(request, f'Fee Category {category.name} updated successfully!')
            return redirect('fees:category_list')
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
    
    context = {
        'page_title': f'Edit {category.name}',
        'category': category,
    }
    return render(request, 'fees/category_form.html', context)


# Fee Structure Views
@login_required
@user_passes_test(is_admin)
def structure_list(request):
    """List all fee structures"""
    structures = FeeStructure.objects.select_related('category', 'department', 'semester').all()
    
    context = {
        'page_title': 'Fee Structures',
        'structures': structures,
    }
    return render(request, 'fees/structure_list.html', context)


@login_required
@user_passes_test(is_admin)
def structure_create(request):
    """Create a new fee structure"""
    if request.method == 'POST':
        try:
            structure = FeeStructure(
                category_id=request.POST.get('category'),
                department_id=request.POST.get('department') or None,
                level=request.POST.get('level', ''),
                semester_id=request.POST.get('semester') or None,
                amount=request.POST.get('amount'),
                frequency=request.POST.get('frequency', 'per_semester'),
                late_fee=request.POST.get('late_fee') or 0,
                late_fee_per_day=request.POST.get('late_fee_per_day') or 0,
                effective_from=request.POST.get('effective_from'),
                effective_to=request.POST.get('effective_to') or None,
            )
            structure.save()
            
            messages.success(request, 'Fee structure created successfully!')
            return redirect('fees:structure_list')
        except Exception as e:
            messages.error(request, f'Error creating structure: {str(e)}')
    
    categories = FeeCategory.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Add Fee Structure',
        'categories': categories,
        'departments': departments,
        'semesters': semesters,
    }
    return render(request, 'fees/structure_form.html', context)


@login_required
@user_passes_test(is_admin)
def structure_update(request, pk):
    """Update a fee structure"""
    structure = get_object_or_404(FeeStructure, pk=pk)
    
    if request.method == 'POST':
        try:
            structure.category_id = request.POST.get('category')
            structure.department_id = request.POST.get('department') or None
            structure.level = request.POST.get('level', '')
            structure.semester_id = request.POST.get('semester') or None
            structure.amount = request.POST.get('amount')
            structure.frequency = request.POST.get('frequency', 'per_semester')
            structure.late_fee = request.POST.get('late_fee') or 0
            structure.late_fee_per_day = request.POST.get('late_fee_per_day') or 0
            structure.effective_from = request.POST.get('effective_from')
            structure.effective_to = request.POST.get('effective_to') or None
            structure.is_active = 'is_active' in request.POST
            structure.save()
            
            messages.success(request, 'Fee structure updated successfully!')
            return redirect('fees:structure_list')
        except Exception as e:
            messages.error(request, f'Error updating structure: {str(e)}')
    
    categories = FeeCategory.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Edit Fee Structure',
        'structure': structure,
        'categories': categories,
        'departments': departments,
        'semesters': semesters,
    }
    return render(request, 'fees/structure_form.html', context)


# Invoice Views
@login_required
@user_passes_test(is_admin)
def invoice_list(request):
    """List all invoices"""
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    
    invoices = Invoice.objects.select_related('student', 'semester').all()
    
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query)
        )
    
    if status:
        invoices = invoices.filter(status=status)
    
    paginator = Paginator(invoices, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Fees Management',
        'invoices': page_obj,
        'payments': Payment.objects.select_related('invoice', 'invoice__student').all()[:50],
        'structures': FeeStructure.objects.select_related('category', 'course').all()[:20],
        'categories': FeeCategory.objects.all()[:20],
        'query': query,
        'selected_status': status,
    }
    return render(request, 'fees/fees_list.html', context)


@login_required
@user_passes_test(is_admin)
def invoice_create(request):
    """Create a new invoice"""
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student')
            semester_id = request.POST.get('semester')
            
            invoice = Invoice(
                student_id=student_id,
                semester_id=semester_id,
                issue_date=request.POST.get('issue_date'),
                due_date=request.POST.get('due_date'),
                subtotal=request.POST.get('subtotal', 0),
                discount=request.POST.get('discount', 0),
                notes=request.POST.get('notes', ''),
                status='issued',
            )
            invoice.save()
            
            # Add invoice items
            descriptions = request.POST.getlist('description')
            amounts = request.POST.getlist('amount')
            
            for i, desc in enumerate(descriptions):
                if desc and i < len(amounts):
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=desc,
                        unit_price=amounts[i],
                        amount=amounts[i],
                    )
            
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
            return redirect('fees:invoice_detail', pk=invoice.pk)
        except Exception as e:
            messages.error(request, f'Error creating invoice: {str(e)}')
    
    students = Student.objects.filter(status='active')
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Create Invoice',
        'students': students,
        'semesters': semesters,
    }
    return render(request, 'fees/invoice_form.html', context)


@login_required
@user_passes_test(is_admin)
def invoice_detail(request, pk):
    """View invoice details"""
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()
    payments = invoice.payments.all()
    
    context = {
        'page_title': f'Invoice {invoice.invoice_number}',
        'invoice': invoice,
        'items': items,
        'payments': payments,
    }
    return render(request, 'fees/invoice_detail.html', context)


@login_required
@user_passes_test(is_admin)
def invoice_update(request, pk):
    """Update an invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        try:
            invoice.issue_date = request.POST.get('issue_date')
            invoice.due_date = request.POST.get('due_date')
            invoice.subtotal = request.POST.get('subtotal', 0)
            invoice.discount = request.POST.get('discount', 0)
            invoice.notes = request.POST.get('notes', '')
            invoice.save()
            
            messages.success(request, f'Invoice {invoice.invoice_number} updated successfully!')
            return redirect('fees:invoice_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error updating invoice: {str(e)}')
    
    context = {
        'page_title': f'Edit Invoice {invoice.invoice_number}',
        'invoice': invoice,
    }
    return render(request, 'fees/invoice_form.html', context)


@login_required
@user_passes_test(is_admin)
def invoice_delete(request, pk):
    """Delete an invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted successfully!')
        return redirect('fees:invoice_list')
    
    context = {
        'page_title': 'Delete Invoice',
        'invoice': invoice,
    }
    return render(request, 'fees/invoice_confirm_delete.html', context)


# Payment Views
@login_required
@user_passes_test(is_admin)
def payment_list(request):
    """List all payments"""
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    
    payments = Payment.objects.select_related('invoice', 'student').all()
    
    if query:
        payments = payments.filter(
            Q(payment_number__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(transaction_id__icontains=query)
        )
    
    if status:
        payments = payments.filter(status=status)
    
    paginator = Paginator(payments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Payments',
        'page_obj': page_obj,
        'query': query,
        'selected_status': status,
    }
    return render(request, 'fees/payment_list.html', context)


@login_required
@user_passes_test(is_admin)
def payment_create(request):
    """Create a new payment"""
    if request.method == 'POST':
        try:
            invoice_id = request.POST.get('invoice')
            invoice = Invoice.objects.get(pk=invoice_id)
            
            payment = Payment(
                invoice=invoice,
                student=invoice.student,
                amount=request.POST.get('amount'),
                payment_method=request.POST.get('payment_method'),
                transaction_id=request.POST.get('transaction_id', ''),
                bank_name=request.POST.get('bank_name', ''),
                reference_number=request.POST.get('reference_number', ''),
                payment_date=timezone.now(),
                received_by=request.user.teacher if hasattr(request.user, 'teacher') else None,
                status='pending',
            )
            payment.save()
            
            # Update invoice
            invoice.amount_paid += payment.amount
            invoice.save()
            
            messages.success(request, f'Payment {payment.payment_number} recorded successfully!')
            return redirect('fees:payment_detail', pk=payment.pk)
        except Exception as e:
            messages.error(request, f'Error creating payment: {str(e)}')
    
    invoices = Invoice.objects.filter(status__in=['issued', 'partial'])
    context = {
        'page_title': 'Record Payment',
        'invoices': invoices,
    }
    return render(request, 'fees/payment_form.html', context)


@login_required
@user_passes_test(is_admin)
def payment_detail(request, pk):
    """View payment details"""
    payment = get_object_or_404(Payment, pk=pk)
    
    context = {
        'page_title': f'Payment {payment.payment_number}',
        'payment': payment,
    }
    return render(request, 'fees/payment_detail.html', context)


@login_required
@user_passes_test(is_admin)
def payment_verify(request, pk):
    """Verify a payment"""
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        payment.status = 'verified'
        payment.verified_by = request.user.teacher if hasattr(request.user, 'teacher') else None
        payment.verified_at = timezone.now()
        payment.save()
        
        messages.success(request, 'Payment verified successfully!')
        return redirect('fees:payment_detail', pk=pk)
    
    context = {
        'page_title': 'Verify Payment',
        'payment': payment,
    }
    return render(request, 'fees/payment_verify.html', context)


# Student Fee Views
@login_required
@user_passes_test(is_student)
def student_fees(request):
    """View student's fee status"""
    student = request.user.student
    
    invoices = Invoice.objects.filter(student=student).order_by('-created_at')
    total_payable = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = invoices.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    balance = total_payable - total_paid
    
    context = {
        'page_title': 'My Fees',
        'invoices': invoices,
        'total_payable': total_payable,
        'total_paid': total_paid,
        'balance': balance,
    }
    return render(request, 'fees/student_fees.html', context)


@login_required
@user_passes_test(is_student)
def student_pay(request):
    """Make a payment"""
    student = request.user.student
    
    if request.method == 'POST':
        try:
            invoice_id = request.POST.get('invoice')
            amount = request.POST.get('amount')
            method = request.POST.get('payment_method')
            
            invoice = Invoice.objects.get(pk=invoice_id, student=student)
            
            payment = Payment(
                invoice=invoice,
                student=student,
                amount=amount,
                payment_method=method,
                transaction_id=request.POST.get('transaction_id', ''),
                payment_date=timezone.now(),
                status='pending',
            )
            payment.save()
            
            messages.success(request, 'Payment initiated successfully!')
            return redirect('fees:student_fees')
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    invoices = Invoice.objects.filter(student=student, status__in=['issued', 'partial'])
    
    context = {
        'page_title': 'Make Payment',
        'invoices': invoices,
    }
    return render(request, 'fees/student_pay.html', context)
