# Generated by Django 3.2.8 on 2021-11-03 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("twoops", "0009_tweet_retweeted_user_screen_name"),
    ]

    operations = [
        migrations.RenameField(
            model_name="tweet",
            old_name="likes_count",
            new_name="favorite_count",
        ),
        migrations.RenameField(
            model_name="tweet",
            old_name="replies_count",
            new_name="reply_count",
        ),
        migrations.RenameField(
            model_name="tweet",
            old_name="retweets_count",
            new_name="retweet_count",
        ),
        migrations.AddField(
            model_name="tweet",
            name="quote_count",
            field=models.IntegerField(default=0),
        ),
    ]
