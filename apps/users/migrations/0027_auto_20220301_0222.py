# Generated by Django 2.1.4 on 2022-03-01 02:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0026_user_device_token'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='device_token',
        ),
        migrations.AddField(
            model_name='devices',
            name='device_token',
            field=models.CharField(blank=True, db_index=True, default=None, max_length=255, null=True, verbose_name='通知Token'),
        ),
    ]
