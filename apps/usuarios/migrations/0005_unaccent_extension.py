from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_user_whatsapp'),
    ]

    operations = [
        UnaccentExtension(),
    ]
