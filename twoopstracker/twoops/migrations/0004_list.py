# Generated by Django 3.2.8 on 2021-11-01 10:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twoops", "0003_userprofile"),
    ]

    operations = [
        migrations.CreateModel(
            name="TwitterAccountsList",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "name",
                    models.CharField(help_text="Name of Twitter List", max_length=255),
                ),
                (
                    "slug",
                    models.CharField(help_text="Twitter List Slug", max_length=255),
                ),
                (
                    "accounts",
                    models.ManyToManyField(
                        related_name="lists", to="twoops.TwitterAccount"
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="twoops.userprofile",
                    ),
                ),
                migrations.AddField(
                    model_name="twitteraccountslist",
                    name="is_private",
                    field=models.BooleanField(default=False),
                ),
            ],
            options={
                "get_latest_by": "updated_at",
                "abstract": False,
            },
        ),
    ]
