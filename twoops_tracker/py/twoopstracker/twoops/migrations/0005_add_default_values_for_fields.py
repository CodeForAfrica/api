# Generated by Django 3.2.8 on 2021-11-03 16:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("twoops", "0004_list"),
    ]

    operations = [
        migrations.AlterField(
            model_name="twitteraccount",
            name="favourites_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="twitteraccount",
            name="followers_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="twitteraccount",
            name="friends_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="twitteraccount",
            name="statuses_count",
            field=models.IntegerField(default=0),
        ),
    ]
