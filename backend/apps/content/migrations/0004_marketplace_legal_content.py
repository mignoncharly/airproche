from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("content", "0003_businesssettings_cancellation_deadline_hours")]
    operations = [
        migrations.AlterField(
            model_name="legaldocument",
            name="kind",
            field=models.CharField(choices=[("privacy", "Privacy policy"), ("terms", "Terms and conditions"), ("cancellation", "Cancellation policy"), ("legal_notice", "Legal notice"), ("cookies", "Cookie policy"), ("transparency", "Platform transparency")], max_length=24),
        ),
    ]
