from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from .forms import AdvanceForm, ExpenseForm, ProjectForm
from .models import Advance, Expense, Project


def _role(user):
    profile = getattr(user, 'profile', None)
    return profile.role if profile else 'ENGINEER'


@login_required
def dashboard(request):
    advances = Advance.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    approved = Expense.objects.filter(status='APPROVED').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    pending = Expense.objects.filter(status='SUBMITTED').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    recent = Expense.objects.select_related('project', 'spent_by').order_by('-created_at')[:8]
    return render(request, 'expenses/dashboard.html', {
        'advance_total': advances, 'approved_total': approved,
        'pending_total': pending, 'balance': advances - approved, 'recent_expenses': recent,
        'role': _role(request.user),
    })
@login_required
def project_list(request):
    return render(request, 'expenses/project_list.html', {'projects': Project.objects.all()})


@login_required
def project_create(request):
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Project created successfully.')
        return redirect('project_list')
    return render(request, 'expenses/form.html', {'form': form, 'title': 'New Project'})


@login_required
def advance_list(request):
    advances = Advance.objects.select_related('project', 'recipient').order_by('-date')
    return render(request, 'expenses/advance_list.html', {'advances': advances})


@login_required
def advance_create(request):
    form = AdvanceForm(request.POST or None)
    if form.is_valid():
        advance = form.save(commit=False)
        advance.created_by = request.user
        advance.save()
        messages.success(request, 'Advance recorded.')
        return redirect('advance_list')
    return render(request, 'expenses/form.html', {'form': form, 'title': 'Record Advance'})
@login_required
def expense_list(request):
    expenses = Expense.objects.select_related('project', 'spent_by').order_by('-date', '-created_at')
    return render(request, 'expenses/expense_list.html', {'expenses': expenses})


@login_required
def expense_create(request):
    form = ExpenseForm(request.POST or None)
    if form.is_valid():
        expense = form.save()
        expense.status = 'SUBMITTED'
        expense.save(update_fields=['status'])
        messages.success(request, 'Expense submitted for approval.')
        return redirect('expense_list')
    return render(request, 'expenses/form.html', {'form': form, 'title': 'Record Expense'})
@login_required
def reconciliation(request):
    advances = Advance.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    expenses = Expense.objects.filter(status='APPROVED').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    return render(request, 'expenses/reconciliation.html', {
        'advances': advances,
        'expenses': expenses,
        'balance': advances - expenses,
    })
