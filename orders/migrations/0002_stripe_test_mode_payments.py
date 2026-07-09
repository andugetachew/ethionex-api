from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("orders", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending Payment"),
                    ("paid", "Paid"),
                    ("processing", "Processing"),
                    ("shipped", "Shipped"),
                    ("delivered", "Delivered"),
                    ("cancelled", "Cancelled"),
                    ("refunded", "Refunded"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("cash", "Cash on Delivery"),
                    ("telebirr", "Telebirr"),
                    ("chapa", "Chapa"),
                    ("bank", "Bank Transfer"),
                    ("stripe", "Stripe (Test Mode)"),
                ],
                default="cash",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="stripe_checkout_session_id",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="stripe_payment_intent_id",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="paid_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
