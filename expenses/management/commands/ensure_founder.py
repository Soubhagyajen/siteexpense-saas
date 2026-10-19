import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from expenses.models import Profile


class Command(BaseCommand):
    help = (
        "Ensure the initial Founder account exists and matches the credentials "
        "configured in the deployment environment."
    )

    def handle(self, *args, **options):
        username = os.environ.get("FOUNDER_USERNAME", "").strip()
        email = os.environ.get("FOUNDER_EMAIL", "").strip()
        password = os.environ.get("FOUNDER_PASSWORD", "")

        if not username or not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Founder bootstrap skipped: set FOUNDER_USERNAME, FOUNDER_EMAIL "
                    "and FOUNDER_PASSWORD in the deployment environment."
                )
            )
            return

        if len(password) < 8:
            raise CommandError("FOUNDER_PASSWORD must contain at least 8 characters.")

        User = get_user_model()

        with transaction.atomic():
            user = User.objects.filter(username=username).first()

            if user is None:
                user = User(username=username)
                action = "created"
            else:
                action = "synchronized"

            # Ensure the account is usable for the initial Founder login.
            user.email = email
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()

            Profile.objects.update_or_create(
                user=user,
                defaults={"role": "FOUNDER"},
            )

        # Never log or print the password.
        self.stdout.write(
            self.style.SUCCESS(
                f"Founder account '{username}' {action}; credentials synchronized "
                "from deployment environment and role set to FOUNDER."
            )
        )
