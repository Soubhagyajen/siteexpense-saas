from django import forms
from .models import Project, Advance, Expense, DebitVoucher


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'code', 'location', 'active']


class AdvanceForm(forms.ModelForm):
    class Meta:
        model = Advance
        fields = ['recipient', 'project', 'amount', 'date', 'reference', 'notes']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'project', 'spent_by', 'category', 'amount', 'date',
            'description', 'vendor', 'payment_mode', 'receipt',
        ]
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}


class VoucherForm(forms.ModelForm):
    class Meta:
        model = DebitVoucher
        fields = ['voucher_no', 'submitted_by', 'status', 'remarks']
