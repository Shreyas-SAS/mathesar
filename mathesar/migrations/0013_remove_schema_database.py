# Generated by Django 3.1.7 on 2021-07-13 23:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mathesar', '0012_transfer_database'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schema',
            name='database',
            field=models.CharField(max_length=128, default=None),
        ),
        migrations.AlterField(
            model_name='schema',
            name='database',
            field=models.CharField(max_length=128, default='mathesar_tables'),
        ),
        migrations.RemoveField(
            model_name='schema',
            name='database',
        ),
    ]
