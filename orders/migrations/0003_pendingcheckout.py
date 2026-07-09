from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_stripe_test_mode_payments"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PendingCheckout",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("stripe", "Stripe (Test Mode)"),
                            ("chapa", "Chapa (Simulated)"),
                        ],
                        default="stripe",
                        max_length=20,
                    ),
                ),
                ("provider_reference", models.CharField(max_length=200, unique=True)),
                ("cart_snapshot", models.JSONField()),
                ("payment_method", models.CharField(default="stripe", max_length=20)),
                ("full_name", models.CharField(max_length=100)),
                ("phone_number", models.CharField(max_length=15)),
                ("address", models.TextField()),
                ("city", models.CharField(max_length=100)),
                ("sub_city", models.CharField(blank=True, max_length=100)),
                ("notes", models.TextField(blank=True)),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "delivery_fee",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("total", models.DecimalField(decimal_places=2, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
