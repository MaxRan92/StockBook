# Generated by Django 3.2.13 on 2022-05-28 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stockdata', '0002_alter_stockinfo_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='sentiment',
            field=models.CharField(choices=[('BULL', 'Bullish'), ('HOLD', 'Hold'), ('BEAR', 'Bearish')], default='HOLD', max_length=9),
        ),
    ]
