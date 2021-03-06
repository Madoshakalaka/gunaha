#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
manage.py importdictionary
"""

import argparse

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Imports the Onespot-Sapir vocabulary list"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--purge",
            action="store_true",
            help=(
                "Deletes ALL of the existing content imported to the database; "
                "do this only if you know what you're doing!"
            ),
        )

    def handle(self, *args, **options) -> None:
        # Import here because I'm assuming there will be weird Django side-effects
        # otherwise :/
        from apps.gunaha.import_dictionary import (
            import_dictionary,
            DictionaryImportError,
        )

        try:
            import_dictionary(purge=options["purge"])
        except DictionaryImportError as error:
            raise CommandError(str(error))
