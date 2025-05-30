# Generated by Django 5.1.7 on 2025-05-13 22:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_user_balance_delete_review'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Баланс'),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_intent_id', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Платёж',
                'verbose_name_plural': 'Платежи',
            },
        ),
    ]
