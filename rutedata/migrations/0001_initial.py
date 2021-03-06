# Generated by Django 2.2.1 on 2020-01-18 13:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('TransportMode', models.CharField(blank=True, max_length=200, null=True)),
                ('TransportSubmode', models.CharField(blank=True, max_length=200, null=True)),
                ('PublicCode', models.CharField(blank=True, max_length=200, null=True, verbose_name='Linjenummer')),
                ('OperatorRef', models.CharField(blank=True, max_length=200, null=True, verbose_name='Operatør')),
                ('RepresentedByGroupRef', models.CharField(blank=True, max_length=200, null=True)),
                ('Colour', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Quay',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('ImportedId', models.CharField(blank=True, max_length=200, null=True)),
                ('latitude', models.DecimalField(decimal_places=8, max_digits=11)),
                ('longitude', models.DecimalField(decimal_places=8, max_digits=11)),
                ('PublicCode', models.CharField(blank=True, max_length=20, null=True)),
                ('Description', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'ordering': ['Stop__Name'],
            },
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('ShortName', models.CharField(blank=True, max_length=200, null=True)),
                ('LineRef', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rutedata.Line')),
                ('destination', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='route_destination', to='rutedata.Quay')),
                ('origin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='route_origin', to='rutedata.Quay')),
            ],
        ),
        migrations.CreateModel(
            name='Stop',
            fields=[
                ('id', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('Name', models.CharField(max_length=200)),
                ('Description', models.CharField(blank=True, max_length=200, null=True)),
                ('latitude', models.DecimalField(decimal_places=8, max_digits=11)),
                ('longitude', models.DecimalField(decimal_places=8, max_digits=11)),
                ('Zone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Sone')),
                ('TransportMode', models.CharField(blank=True, max_length=200, null=True)),
                ('TopographicPlace', models.CharField(blank=True, max_length=200, null=True)),
                ('Adjacent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='adjacent', to='rutedata.Stop')),
                ('Parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='rutedata.Stop')),
            ],
            options={
                'ordering': ['Name'],
            },
        ),
        migrations.CreateModel(
            name='ServiceJourney',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('private_code', models.CharField(max_length=8)),
                ('line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rutedata.Line')),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rutedata.Route')),
            ],
        ),
        migrations.AddField(
            model_name='quay',
            name='Stop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quays', to='rutedata.Stop'),
        ),
        migrations.CreateModel(
            name='PointOnRoute',
            fields=[
                ('id', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('order', models.IntegerField(verbose_name='Rekkefølge')),
                ('Route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rutedata.Route')),
                ('quay', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='rutedata.Quay')),
            ],
        ),
        migrations.CreateModel(
            name='PassingTime',
            fields=[
                ('id', models.CharField(max_length=60, primary_key=True, serialize=False)),
                ('departure_time', models.TimeField(blank=True, null=True)),
                ('arrival_time', models.TimeField(blank=True, null=True)),
                ('point', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rutedata.PointOnRoute')),
                ('service_journey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rutedata.ServiceJourney')),
            ],
        ),
        migrations.CreateModel(
            name='GroupOfStopPlaces',
            fields=[
                ('id', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('latitude', models.DecimalField(decimal_places=8, max_digits=11)),
                ('longitude', models.DecimalField(decimal_places=8, max_digits=11)),
                ('members', models.ManyToManyField(related_name='groups', to='rutedata.Stop')),
            ],
        ),
    ]
