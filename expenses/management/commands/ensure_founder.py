import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from expenses.models import Profile


class Command(BaseCommand):
    help = "Create the initial Founder account from environment variables if it does not exist."

    def handle(self, *args, **options):
        username = os.environ.get("FOUNDER_USERNAME", "").strip()
        email = os.environ.get("FOUNDER_EMAIL", "").strip()
        password = os.environ.get("FOUNDER_PASSWORD", "")

        if not username or not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Founder bootstrap skipped: set FOUNDER_USERNAME, FOUNDER_EMAIL and "
                    "FOUNDER_PASSWORD in the deployment environment."
                )
            )
            return

        if len(password) < 8:
            raise CommandError("FOUNDER_PASSWORD must contain at least 8 characters.")

        User = get_user_model()
        user = User.objects.filter(username=username).first()

        if user is None:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True,
            )
            Profile.objects.update_or_create(
                user=user,
                defaults={"role": "FOUNDER"},
            )
            self.stdout.write(
                self.style.SUCCESS(f"Founder account '{username}' created.")
            )
            return

        changed = False

        if user.email != email:
            user.email = email
            changed = True

        if not user.is_staff:
            user.is_staff = True
            changed = True

        if not user.is_superuser:
            user.is_superuser = True
            changed = True

        if changed:
            user.save(update_fields=["email", "is_staff", "is_superuser"])

        Profile.objects.update_or_create(
            user=user,
            defaults={"role": "FOUNDER"},
        )

        self.stdout.write(
            self.style.SUCCESS(f"Founder account '{username}' already exists; access verified.")
        )
