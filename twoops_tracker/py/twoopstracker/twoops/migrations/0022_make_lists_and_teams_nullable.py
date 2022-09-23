# Generated by Django 3.2.11 on 2022-02-15 13:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twoops", "0021_twitteraccount_profile_image_url_https"),
    ]

    operations = [
        migrations.AlterField(
            model_name="team",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                help_text="Owner of the group",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="twoops.userprofile",
            ),
        ),
        migrations.AlterField(
            model_name="twitteraccountslist",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="twoops.userprofile",
            ),
        ),
    ]