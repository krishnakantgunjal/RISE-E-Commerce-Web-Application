from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Create or reset admin user"

    def handle(self, *args, **kwargs):
        username = "krish"
        email = "krish@example.com"
        password = "12345678"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )

        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS("Admin user created"))
        else:
            self.stdout.write(self.style.SUCCESS("Admin password reset"))
