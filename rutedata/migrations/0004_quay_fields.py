# Generated by Django 3.1.5 on 2021-05-15 20:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rutedata', '0003_lat_lon_null'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quay',
            name='name',
        ),
        migrations.AlterField(
            model_name='quay',
            name='Stop',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quays', to='rutedata.stop'),
        ),
    ]