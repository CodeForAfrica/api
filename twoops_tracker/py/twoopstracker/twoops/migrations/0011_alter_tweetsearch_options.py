# Generated by Django 3.2.8 on 2021-11-22 04:59

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("twoops", "0010_tweetsearch"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="tweetsearch",
            options={"verbose_name_plural": "Tweet Searches"},
        ),
    ]
