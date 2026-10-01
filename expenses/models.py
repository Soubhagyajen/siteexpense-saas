from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator


class Profile(models.Model):
    ROLE_CHOICES = [
        ('FOUNDER', 'Founder'),
        ('MANAGER', 'Manager'),
        ('ENGINEER', 'Engineer'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ENGINEER')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role}"


class Project(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Advance(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.PROTECT, related_name='advances')
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='advances')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_advances')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Advance #{self.pk} - ₹{self.amount}"


class Expense(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    CATEGORY_CHOICES = [
        ('MATERIAL', 'Material'),
        ('LABOUR', 'Labour'),
        ('TRAVEL', 'Travel'),
        ('FOOD', 'Food'),
        ('TOOLS', 'Tools'),
        ('SITE', 'Site Expense'),
        ('OTHER', 'Other'),
    ]
    PAYMENT_CHOICES = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI'),
        ('CARD', 'Card'),
        ('BANK', 'Bank Transfer'),
    ]
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='expenses')
    advance = models.ForeignKey(
        Advance, on_delete=models.PROTECT, null=True, blank=True, related_name='expenses'
    )
    spent_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='expenses')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateField()
    description = models.CharField(max_length=255)
    vendor = models.CharField(max_length=150, blank=True)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='CASH')
    receipt = models.FileField(upload_to='receipts/%Y/%m/', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        related_name='approved_expenses'
    )

    def __str__(self):
        return f"Expense #{self.pk} - ₹{self.amount}"


class DebitVoucher(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    expense = models.OneToOneField(Expense, on_delete=models.CASCADE, related_name='voucher')
    voucher_no = models.CharField(max_length=40, unique=True)
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='submitted_vouchers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    approved_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        related_name='approved_vouchers'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.voucher_no


class LedgerEntry(models.Model):
    ENTRY_CHOICES = [('DEBIT', 'Debit'), ('CREDIT', 'Credit')]
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='ledger_entries')
    date = models.DateField()
    account = models.CharField(max_length=150)
    entry_type = models.CharField(max_length=10, choices=ENTRY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    narration = models.CharField(max_length=255)
    expense = models.ForeignKey(Expense, null=True, blank=True, on_delete=models.SET_NULL)
    advance = models.ForeignKey(Advance, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class MonthlyReconciliation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='reconciliations')
    month = models.DateField(help_text='Use the first day of the month')
    opening_advance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_advance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'month')
        ordering = ['-month']

    def calculate_balance(self):
        return self.opening_advance + self.total_advance - self.total_expense

    def save(self, *args, **kwargs):
        self.closing_balance = self.calculate_balance()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project.code} - {self.month:%B %Y}"
