# Generated by Django 2.1.4 on 2021-09-10 06:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manage', '0003_payconfig_test_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppPlatform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, default=None, max_length=128, null=True, verbose_name='平台名字')),
                ('platform_id', models.CharField(blank=True, db_index=True, default=None, max_length=64, null=True, unique=True, verbose_name='平台id')),
            ],
            options={
                'verbose_name': '应用平台',
                'verbose_name_plural': '应用平台',
            },
        ),
        migrations.AddField(
            model_name='apppackage',
            name='platform',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='manage.AppPlatform', verbose_name='应用平台'),
        ),
    ]
