# Generated by Django 5.1.7 on 2025-05-20 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_alter_user_balance_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
