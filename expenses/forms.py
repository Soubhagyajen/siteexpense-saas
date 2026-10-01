from django import forms
from .models import Project, Advance, Expense


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
            'project', 'advance', 'spent_by', 'category', 'amount', 'date',
            'description', 'vendor', 'payment_mode', 'receipt',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(attrs={'placeholder': 'What was purchased or paid for?'}),
            'vendor': forms.TextInput(attrs={'placeholder': 'Vendor / shop name'}),
        }

    def clean(self):
        cleaned = super().clean()
        project = cleaned.get('project')
        advance = cleaned.get('advance')
        amount = cleaned.get('amount')
        if advance and project and advance.project_id != project.id:
            self.add_error('advance', 'Select an advance from the same project.')
        if advance and amount and amount > advance.amount:
            self.add_error('amount', 'Expense cannot exceed the selected advance amount.')
        return cleaned
