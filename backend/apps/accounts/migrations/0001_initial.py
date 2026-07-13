# Generated for the initial custom user model. Keep this as the first project migration.
import uuid

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import apps.accounts.managers


class Migration(migrations.Migration):
    initial = True

    dependencies = [("auth", "0012_alter_user_first_name_max_length")]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("first_name", models.CharField(max_length=150)),
                ("last_name", models.CharField(max_length=150)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("preferred_locale", models.CharField(default="fr", max_length=10)),
                ("email_verified_at", models.DateTimeField(blank=True, null=True)),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"abstract": False},
            managers=[("objects", apps.accounts.managers.UserManager())],
        )
    ]

