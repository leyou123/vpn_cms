# Generated by Django 2.1.4 on 2021-09-23 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_auto_20210923_0945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orders',
            name='package_id',
            field=models.CharField(blank=True, db_index=True, default=None, max_length=64, null=True, verbose_name='AppID'),
        ),
    ]
