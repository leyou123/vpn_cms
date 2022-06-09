# Generated by Django 2.1.4 on 2021-09-10 07:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manage', '0007_remove_setmeal_app'),
        ('users', '0004_auto_20210907_1022'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='app',
        ),
        migrations.AddField(
            model_name='user',
            name='platform',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='manage.AppPlatform', verbose_name='应用平台'),
        ),
    ]
