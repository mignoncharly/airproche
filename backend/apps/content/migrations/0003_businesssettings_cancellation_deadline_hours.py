from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("content", "0002_businesssettings_currency_and_more")]

    operations = [
        migrations.AddField(
            model_name="businesssettings",
            name="cancellation_deadline_hours",
            field=models.PositiveSmallIntegerField(default=24),
        ),
    ]
