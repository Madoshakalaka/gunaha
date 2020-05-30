#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import csv
import io
import logging
import re
from collections import defaultdict
from hashlib import sha1, sha384
from pathlib import Path
from typing import Dict, Set, Tuple
from unicodedata import normalize

from django.conf import settings
from django.db import transaction
from django.db.utils import OperationalError

from apps.morphodict.models import Definition, DictionarySource, Head

logger = logging.getLogger(__name__)

private_dir = settings.DATA_DIR / "private"


def import_dictionary(purge: bool = False) -> None:
    Definition2Source = Definition.citations.through

    logger.info("Importing OneSpot-Sapir vocabulary list")

    filename = "Onespot-Sapir-Vocabulary-list-OS-Vocabulary.tsv"
    path_to_tsv = private_dir / filename
    if not path_to_tsv.exists():
        # TODO: raise an error
        logger.warn("Cannot find dictionary file @ %s. Skipping...", path_to_tsv)
        return

    with open(path_to_tsv, "rb") as raw_file:
        raw_bytes = raw_file.read()

    file_hash = sha384(raw_bytes).hexdigest()
    assert len(file_hash) == 384 // 4
    tsv_file = io.StringIO(raw_bytes.decode("UTF-8"))

    logger.info("Importing %s [SHA-384: %s]", path_to_tsv, file_hash)

    # Purge only once we KNOW we have dictionary content

    if purge:
        with transaction.atomic():
            logger.warn("Purging ALL existing dictionary content")
            Definition2Source.objects.all().delete()
            Definition.objects.all().delete()
            Head.objects.all().delete()
            DictionarySource.objects.all().delete()

    if not should_import_onespot(file_hash):
        logger.info("Already imported %s; skipping...", path_to_tsv)
        return

    onespot = DictionarySource(
        abbrv="Onespot",
        title="Onespot-Sapir vocabulary list",
        editor="Bruce Starlight, John Onespot, Edward Sapir",
        import_filename=filename,
        last_import_sha384=file_hash,
    )

    heads: Dict[int, Head] = {}
    definitions: Dict[int, Definition] = {}
    mappings: Set[Tuple[int, int]] = set()

    entries = csv.DictReader(tsv_file, delimiter="\t")
    for entry in entries:
        term = normalize_orthography(entry["Bruce - Tsuut'ina text"])

        if should_skip_importing_head(term):
            continue

        word_class = entry["Part of speech"]
        primary_key = make_primary_key(term, word_class)
        head = heads.setdefault(
            primary_key, Head(pk=primary_key, text=term, word_class=word_class)
        )

        # TODO: tag certain words as "not suitable for school" -- I guess NSFW?
        # TODO: tag heads with "Folio" -- more specifically where the word came from

        definition = nfc(entry["Bruce - English text"])
        if not definition:
            continue

        pk = make_primary_key(definition, str(head.pk))
        dfn = Definition(pk=pk, text=definition, defines=head)
        definitions[pk] = dfn
        mappings.add((pk, onespot.pk))

    logger.info(
        "Will insert: heads: %d, defs: %d", len(heads), len(definitions),
    )

    with transaction.atomic():
        DictionarySource.objects.bulk_create([onespot])
        Head.objects.bulk_create(heads.values())
        Definition.objects.bulk_create(definitions.values())
        Definition2Source.objects.bulk_create(
            Definition2Source(definition_id=def_pk, dictionarysource_id=dict_pk)
            for def_pk, dict_pk in mappings
        )

    logger.info("Done importing from %s", path_to_tsv)


def normalize_orthography(tsuutina_word: str) -> str:
    LATIN_SMALL_LETTER_L_WITH_MIDDLE_TIDLE = "\u026B"
    LATIN_SMALL_LETTER_L_WITH_STROKE = "\u0142"
    tsuutina_word = tsuutina_word.strip()
    tsuutina_word = nfc(tsuutina_word)
    # According to Chris Cox: Original mostly used <ɫ>, but writers now prefer
    # <ł>, as it is more distinct from <t>. So let's make it consistent!
    tsuutina_word = tsuutina_word.replace(
        LATIN_SMALL_LETTER_L_WITH_MIDDLE_TIDLE, LATIN_SMALL_LETTER_L_WITH_STROKE
    )
    return tsuutina_word


def nfc(text: str) -> str:
    return normalize("NFC", text)


def should_skip_importing_head(head: str) -> bool:
    if head.startswith("*"):
        logger.debug("Skipping ungrammatical form: %r", head)
        return True
    return False


def make_primary_key(*args: str) -> int:
    number = int(sha1("\n".join(args).encode("UTF-8")).hexdigest(), base=16)
    return number & 0xFFFFFFFF


def should_import_onespot(file_hash: str) -> bool:
    try:
        ds = DictionarySource.objects.get(abbrv="Onespot")
    except OperationalError:
        logger.error("Database does not yet exist...")
        return False
    except DictionarySource.DoesNotExist:
        logger.info("Importing for the first time!")
        return True

    if ds.last_import_sha384 == file_hash:
        return False
    return True
