#!/usr/bin/env python
"""Command-line utility for running Django & company entry point tasks."""

import os
import sys


def celery():
    """Wrap the celery cli tool."""

    try:
        from celery.bin.celery import main as celery_main
    except ImportError as exc:
        raise ImportError(
            "Couldn't import celery. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
            "Couldn't import gunicorn. Are you sure it's installed and "
        ) from exc

    return celery_main()


def gunicorn():
    """Wrap the gunicorn cli tool."""

    try:
        from gunicorn.app.wsgiapp import run as gunicorn_main
    except ImportError as exc:
        raise ImportError(
            "Couldn't import gunicorn. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
            "Couldn't import gunicorn. Are you sure it's installed and "
        ) from exc

    return gunicorn_main()


def manage(settings_module):
    """Run administrative tasks."""

    if settings_module:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    args = sys.argv
    if len(sys.argv) == 2 and sys.argv[1] == "runserver":
        # We rely on Pants's reloading, so turn off Django's (which doesn't interact
        # well with Pex: Pex's re-exec logic causes Django's re-exec to misdetect its
        # entry point, see https://code.djangoproject.com/ticket/32314).
        # TODO: Some way to detect that we're in a `./pants run`, and only set
        # --noreload in that case, so that users can run manage.py directly if
        # they want to.
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


def main(*, settings_module=None):
    if len(sys.argv) > 1:
        sys.argv = sys.argv[1:]
        if sys.argv[0] == "manage":
            manage(settings_module)
        elif sys.argv[0] == "celery":
            celery()
        elif sys.argv[0] == "gunicorn":
            gunicorn()
        else:
            print(f"Unknown command: {sys.argv[0]}")


if __name__ == "__main__":
    main()
