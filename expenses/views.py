from decimal import Decimal
from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import AdvanceForm, ExpenseForm, ProjectForm
from .models import Advance, DebitVoucher, Expense, LedgerEntry, Project


def _role(user):
    profile = getattr(user, 'profile', None)
    return profile.role if profile else 'ENGINEER'


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(request, *args, **kwargs):
            if _role(request.user) not in roles:
                return HttpResponseForbidden('You do not have permission for this action.')
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def _voucher_no(expense):
    return f"DV-{timezone.now():%Y%m%d}-{expense.pk:05d}"
@login_required
def dashboard(request):
    advances = Advance.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    approved = Expense.objects.filter(status='APPROVED').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    pending = Expense.objects.filter(status='SUBMITTED').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    recent = Expense.objects.select_related('project', 'spent_by').order_by('-created_at')[:8]
    pending_reviews = Expense.objects.filter(status='SUBMITTED').select_related(
        'project', 'spent_by', 'advance'
    ).order_by('date', 'created_at')[:5]
    return render(request, 'expenses/dashboard.html', {
        'advance_total': advances,
        'approved_total': approved,
        'pending_total': pending,
        'balance': advances - approved,
        'recent_expenses': recent,
        'pending_reviews': pending_reviews,
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
@role_required('FOUNDER', 'MANAGER')
def advance_list(request):
    advances = Advance.objects.select_related('project', 'recipient', 'created_by').order_by('-date', '-created_at')
    return render(request, 'expenses/advance_list.html', {'advances': advances})


@role_required('FOUNDER', 'MANAGER')
def advance_create(request):
    form = AdvanceForm(request.POST or None)
    if form.is_valid():
        with transaction.atomic():
            advance = form.save(commit=False)
            advance.created_by = request.user
            advance.save()
            LedgerEntry.objects.bulk_create([
                LedgerEntry(
                    project=advance.project,
                    date=advance.date,
                    account='Manager Advance',
                    entry_type='DEBIT',
                    amount=advance.amount,
                    narration=f'Advance released to {advance.recipient.get_full_name() or advance.recipient.username}',
                    advance=advance,
                ),
                LedgerEntry(
                    project=advance.project,
                    date=advance.date,
                    account='Cash / Bank',
                    entry_type='CREDIT',
                    amount=advance.amount,
                    narration=f'Funds released against advance #{advance.pk}',
                    advance=advance,
                ),
            ])
        messages.success(request, f'Advance of ₹{advance.amount:,.2f} recorded.')
        return redirect('advance_list')
    return render(request, 'expenses/form.html', {'form': form, 'title': 'Record Advance'})
@login_required
def expense_list(request):
    expenses = Expense.objects.select_related('project', 'advance', 'spent_by').prefetch_related('voucher').order_by('-date', '-created_at')
    return render(request, 'expenses/expense_list.html', {
        'expenses': expenses,
        'role': _role(request.user),
    })


@login_required
def expense_create(request):
    form = ExpenseForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        with transaction.atomic():
            expense = form.save(commit=False)
            if _role(request.user) == 'ENGINEER':
                expense.spent_by = request.user
            expense.status = 'SUBMITTED'
            expense.save()
            DebitVoucher.objects.create(
                expense=expense,
                voucher_no=_voucher_no(expense),
                submitted_by=request.user,
                status='PENDING',
            )
        messages.success(request, 'Expense submitted and debit voucher generated.')
        return redirect('expense_detail', pk=expense.pk)
    return render(request, 'expenses/form.html', {
        'form': form,
        'title': 'Record Expense',
        'multipart': True,
    })
@login_required
def expense_detail(request, pk):
    expense = get_object_or_404(
        Expense.objects.select_related('project', 'advance', 'spent_by', 'approved_by').prefetch_related('voucher'),
        pk=pk
    )
    return render(request, 'expenses/expense_detail.html', {
        'expense': expense,
        'role': _role(request.user),
    })


@role_required('FOUNDER')
def approve_expense(request, pk):
    if request.method != 'POST':
        return redirect('expense_detail', pk=pk)
    with transaction.atomic():
        expense = get_object_or_404(Expense.objects.select_for_update().select_related('advance'), pk=pk)
        if expense.status != 'SUBMITTED':
            messages.warning(request, 'Only submitted expenses can be approved.')
            return redirect('expense_detail', pk=pk)
        if expense.advance_id:
            used = Expense.objects.filter(
                advance_id=expense.advance_id, status='APPROVED'
            ).exclude(pk=expense.pk).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            if used + expense.amount > expense.advance.amount:
                messages.error(request, 'Approval blocked: this would exceed the selected advance balance.')
                return redirect('expense_detail', pk=pk)
        expense.status = 'APPROVED'
        expense.approved_by = request.user
        expense.approved_at = timezone.now()
        expense.save(update_fields=['status', 'approved_by', 'approved_at'])
        voucher = expense.voucher
        voucher.status = 'APPROVED'
        voucher.approved_by = request.user
        voucher.approved_at = timezone.now()
        voucher.save(update_fields=['status', 'approved_by', 'approved_at'])
        LedgerEntry.objects.bulk_create([
            LedgerEntry(
                project=expense.project,
                date=expense.date,
                account=f'Site Expense - {expense.get_category_display()}',
                entry_type='DEBIT',
                amount=expense.amount,
                narration=expense.description,
                expense=expense,
            ),
            LedgerEntry(
                project=expense.project,
                date=expense.date,
                account='Manager Advance',
                entry_type='CREDIT',
                amount=expense.amount,
                narration=f'Advance adjusted against {voucher.voucher_no}',
                expense=expense,
                advance=expense.advance,
            ),
        ])
    messages.success(request, f'{expense.voucher.voucher_no} approved and posted to ledger.')
    return redirect('expense_detail', pk=pk)


@role_required('FOUNDER')
def reject_expense(request, pk):
    if request.method != 'POST':
        return redirect('expense_detail', pk=pk)
    expense = get_object_or_404(Expense.objects.select_related('voucher'), pk=pk)
    if expense.status == 'SUBMITTED':
        expense.status = 'REJECTED'
        expense.save(update_fields=['status'])
        voucher = expense.voucher
        voucher.status = 'REJECTED'
        voucher.approved_by = request.user
        voucher.approved_at = timezone.now()
        voucher.remarks = request.POST.get('remarks', '').strip()
        voucher.save(update_fields=['status', 'approved_by', 'approved_at', 'remarks'])
        messages.success(request, 'Expense rejected.')
    return redirect('expense_detail', pk=pk)
@login_required
def voucher_detail(request, pk):
    voucher = get_object_or_404(
        DebitVoucher.objects.select_related(
            'expense__project', 'expense__advance', 'expense__spent_by',
            'submitted_by', 'approved_by'
        ),
        pk=pk
    )
    return render(request, 'expenses/voucher_detail.html', {'voucher': voucher, 'role': _role(request.user)})


@role_required('FOUNDER', 'MANAGER')
def ledger(request):
    entries = LedgerEntry.objects.select_related('project', 'expense', 'advance').order_by('-date', '-created_at')
    return render(request, 'expenses/ledger.html', {'entries': entries[:200]})


@login_required
def reconciliation(request):
    projects = Project.objects.filter(active=True).order_by('code')
    project_id = request.GET.get('project')
    project = get_object_or_404(Project, pk=project_id) if project_id else projects.first()
    if not project:
        return render(request, 'expenses/reconciliation.html', {
            'projects': projects, 'project': None,
            'month_value': timezone.localdate().strftime('%Y-%m'),
            'opening_balance': Decimal('0'), 'total_advance': Decimal('0'),
            'total_expense': Decimal('0'), 'closing_balance': Decimal('0'),
        })
    month_value = request.GET.get('month') or timezone.localdate().strftime('%Y-%m')
    try:
        year, month = [int(x) for x in month_value.split('-')]
        month_start = timezone.datetime(year, month, 1).date()
    except (ValueError, TypeError):
        month_start = timezone.localdate().replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    opening_adv = Advance.objects.filter(project=project, date__lt=month_start).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    opening_exp = Expense.objects.filter(project=project, status='APPROVED', date__lt=month_start).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_advance = Advance.objects.filter(project=project, date__gte=month_start, date__lt=next_month).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_expense = Expense.objects.filter(project=project, status='APPROVED', date__gte=month_start, date__lt=next_month).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    opening_balance = opening_adv - opening_exp
    closing_balance = opening_balance + total_advance - total_expense
    return render(request, 'expenses/reconciliation.html', {
        'projects': projects,
        'project': project,
        'month_value': month_start.strftime('%Y-%m'),
        'opening_balance': opening_balance,
        'total_advance': total_advance,
        'total_expense': total_expense,
        'closing_balance': closing_balance,
    })
