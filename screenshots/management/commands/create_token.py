from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Create or get an API token for a user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username to create token for")

    def handle(self, *args, **options):
        username = options["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
            return

        token, created = Token.objects.get_or_create(user=user)

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Created new token for user {username}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Token already exists for user {username}")
            )

        self.stdout.write(f"Token: {token.key}")
