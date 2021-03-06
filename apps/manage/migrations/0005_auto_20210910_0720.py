# Generated by Django 2.1.4 on 2021-09-10 07:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manage', '0004_auto_20210910_0632'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='appplatform',
            options={'verbose_name': 'APP平台', 'verbose_name_plural': 'APP平台'},
        ),
        migrations.AddField(
            model_name='setmeal',
            name='platform',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='manage.AppPlatform', verbose_name='应用平台'),
        ),
        migrations.AddField(
            model_name='usersconfig',
            name='platform',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='manage.AppPlatform', verbose_name='应用平台'),
        ),
    ]
