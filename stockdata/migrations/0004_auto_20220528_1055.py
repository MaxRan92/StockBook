# Generated by Django 3.2.13 on 2022-05-28 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stockdata', '0003_comment_sentiment'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockinfo',
            name='bears',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='stockinfo',
            name='bulls',
            field=models.IntegerField(default=0),
        ),
    ]
