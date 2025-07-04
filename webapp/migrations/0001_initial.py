# Generated by Django 5.1.7 on 2025-05-28 00:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FantasyRankedPlayer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=100)),
                ('ppg', models.FloatField()),
                ('rpg', models.FloatField()),
                ('apg', models.FloatField()),
                ('bpg', models.FloatField()),
                ('spg', models.FloatField()),
            ],
        ),
    ]
