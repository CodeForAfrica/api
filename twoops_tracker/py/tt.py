#!/usr/bin/env python
"""TwoopsTracker's command-line utility for running entry point tasks."""
import os
import sys

from celery.bin.celery import main as celery_main
from gunicorn.app.wsgiapp import run as gunicorn_main


def celery():
    """Wrap the celery cli tool."""
    return celery_main()


def gunicorn():
    """Wrap the gunicorn cli tool."""
    return gunicorn_main()


def manage():
    """Run administrative tasks."""

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "twoopstracker.settings")
    args = sys.argv
    if len(sys.argv) == 2 and sys.argv[1] == "runserver":
        # We rely on Pants's reloading, so turn off Django's (which doesn't interact
        # well with Pex: Pex's re-exec logic causes Django's re-exec to misdetect its
        # entry point, see https://code.djangoproject.com/ticket/32314).
        # TODO: Some way to detect that we're in a `./pants run`, and only set --noreload
        #  in that case, so that users can run manage.py directly if they want to.
        args += ["--noreload"]
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(args)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        print(sys.argv)

        sys.argv = sys.argv[1:]
        if sys.argv[0] == "manage":
            manage()
        elif sys.argv[0] == "celery":
            celery()
        elif sys.argv[0] == "gunicorn":
            gunicorn()
        else:
            print(f"Unknown command: {sys.argv[0]}")
