# Generated by Django 5.1.7 on 2025-04-28 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_chat_message'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Open', 'Открыт'), ('InWork', 'В работе'), ('Completed', 'Завершён'), ('Cancelled', 'Отменён')], default='Открыт', max_length=20, verbose_name='Статус'),
        ),
    ]
