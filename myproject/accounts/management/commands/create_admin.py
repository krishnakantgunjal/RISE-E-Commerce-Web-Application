from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create default superuser if not exists"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = "krish"
        email = "krish@example.com"
        password = "12345678"

        if User.objects.filter(username=username).exists():
            self.stdout.write("Superuser already exists")
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write("Superuser created successfully")
