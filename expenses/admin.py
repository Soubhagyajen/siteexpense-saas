from django.contrib import admin
from .models import (
    Profile, Project, Advance, Expense, DebitVoucher,
    LedgerEntry, MonthlyReconciliation,
)

admin.site.register(Profile)
admin.site.register(Project)
admin.site.register(Advance)
admin.site.register(Expense)
admin.site.register(DebitVoucher)
admin.site.register(LedgerEntry)
admin.site.register(MonthlyReconciliation)
