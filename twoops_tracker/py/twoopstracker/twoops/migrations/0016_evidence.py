# Generated by Django 3.2.8 on 2021-12-02 11:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("twoops", "0015_merge_20211201_0313"),
    ]

    operations = [
        migrations.CreateModel(
            name="Evidence",
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
                    "url",
                    models.URLField(
                        help_text=(
                            "URL to evidence showing that this account can belong to a"
                            " public list"
                        )
                    ),
                ),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evidence",
                        to="twoops.twitteraccount",
                    ),
                ),
            ],
            options={
                "get_latest_by": "updated_at",
                "abstract": False,
            },
        ),
    ]
