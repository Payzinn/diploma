# Generated by Django 5.1.7 on 2025-05-11 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_chat_is_active_alter_message_extra_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Open', 'Открыт'), ('InWork', 'В работе'), ('Completed', 'Завершён'), ('Cancelled', 'Отменён'), ('Deleted', 'Удалён')], default='Open', max_length=20, verbose_name='Статус'),
        ),
    ]
