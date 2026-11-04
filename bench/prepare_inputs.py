"""Resolve authenticated local captures, extracted files or original archives."""
import hashlib
import os
import shutil
import zipfile
from pathlib import Path

from audit_ram_v121 import EXPECTED_SHA
from emulate_nand_v121 import EXPECTED_FILES
from full_flash import FULL_SHA, SIZE as FULL_SIZE

FIRMWARE_NAME = 'D578UV_GD_V1.21_20240619.CDD'
FIRMWARE_SIZE = 1020300
APP_OFFSET = 0x6000
OEM_ARCHIVE = 'AT-D578 PRO PC SOFTWARE.zip'
NAND_ARCHIVE = 'D578_PASSATION_PHASE47_NAND_COMPLETE_2026-11-03.zip'
SCT_NAME = 'SCT3258TD_UpdateFlash_V2_01_07BF.hex'
SCT_SIZE = 603102
SCT_SHA = 'd5ada473af891b6c707978f0b9dde81324afcc4af27348d3bcdf70615ab19407'


def file_hash(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def verify_file(path, size, digest):
    path = Path(path)
    if path.stat().st_size != size or file_hash(path) != digest:
        raise ValueError(f'Taille ou empreinte SHA256 inattendue : {path}')
    return path


def extract_verified(archive, filename, destination, size, digest):
    destination = Path(destination)
    if destination.exists():
        return verify_file(destination, size, digest)
    with zipfile.ZipFile(archive) as z:
        entries = [i for i in z.infolist()
                   if not i.is_dir() and i.filename.replace('\\', '/').split('/')[-1] == filename]
        if len(entries) != 1 or entries[0].file_size != size:
            raise ValueError(f'Expected exactly one {filename} with {size} bytes in {archive}')
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + '.part')
        try:
            with z.open(entries[0]) as src, temporary.open('wb') as dst:
                shutil.copyfileobj(src, dst)
            verify_file(temporary, size, digest)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    return destination


def local_input(source, cache, filename, nand=False):
    source, cache = Path(source), Path(cache)
    paths = [cache / 'NAND_ORIGINAUX' / filename] if nand else [cache / filename]
    paths += [source / filename, source / 'NAND_ORIGINAUX' / filename]
    return next((path for path in paths if path.is_file()), None)


def resolve_input(source, cache, filename, size, digest, archive, nand=False):
    source, cache = Path(source), Path(cache)
    destination = cache / 'NAND_ORIGINAUX' / filename if nand else cache / filename
    existing = local_input(source, cache, filename, nand)
    if existing is None:
        return extract_verified(source / archive, filename, destination, size, digest)
    verify_file(existing, size, digest)
    if existing.resolve() == destination.resolve():
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Models open these captures read-only. A link avoids copying 256 MiB on the
    # same filesystem; cross-volume/unsupported links fall back to a byte copy.
    temporary = destination.with_suffix(destination.suffix + '.part')
    try:
        try:
            os.link(existing, temporary)
        except OSError:
            shutil.copyfile(existing, temporary)
        verify_file(temporary, size, digest)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def missing_inputs(source_directory, cache_directory, full_flash=None, bluetooth='absent'):
    """Fast inventory only; execution still authenticates every selected input."""
    source, cache = Path(source_directory), Path(cache_directory)
    flash = Path(full_flash) if full_flash else source / 'full_flash_pass1.bin'
    missing = []
    if not flash.is_file():
        missing.append(str(flash))
    archive_members = {}

    def available(filename, archive, nand=False):
        if local_input(source, cache, filename, nand):
            return True
        path = source / archive
        if not path.is_file():
            return False
        if path not in archive_members:
            try:
                with zipfile.ZipFile(path) as z:
                    archive_members[path] = [i.filename.replace('\\', '/').split('/')[-1]
                                             for i in z.infolist() if not i.is_dir()]
            except zipfile.BadZipFile as error:
                raise ValueError(f'Archive ZIP illisible : {path}') from error
        return archive_members[path].count(filename) == 1

    # The exact reference application can also be recovered from full Flash.
    if not available(FIRMWARE_NAME, OEM_ARCHIVE) and not flash.is_file():
        missing.append(FIRMWARE_NAME + ' (ou full_flash_pass1.bin)')
    for name in EXPECTED_FILES:
        if not available(name, NAND_ARCHIVE, nand=True):
            missing.append(name)
    if not available(SCT_NAME, OEM_ARCHIVE):
        missing.append(SCT_NAME)
    if bluetooth == 'et12' and not available('B707_Audio_AGHF_ET12_QX-V10043.bin', OEM_ARCHIVE):
        missing.append('B707_Audio_AGHF_ET12_QX-V10043.bin')
    return missing


def check_inputs(source_directory, cache_directory, full_flash=None, bluetooth='absent'):
    missing = missing_inputs(source_directory, cache_directory, full_flash, bluetooth)
    if missing:
        raise ValueError('Fichiers manquants : ' + ', '.join(missing) +
                         '. Fournir les fichiers extraits ou les archives d’origine '
                         + OEM_ARCHIVE + ' et ' + NAND_ARCHIVE +
                         '. La NAND principale seule ne contient ni OOB ni relevé ECC.')


def prepare(source_directory, cache_directory, full_flash=None):
    source, cache = Path(source_directory), Path(cache_directory)
    existing = local_input(source, cache, FIRMWARE_NAME)
    archive = source / OEM_ARCHIVE
    if existing or archive.is_file():
        firmware = resolve_input(source, cache, FIRMWARE_NAME, FIRMWARE_SIZE,
                                 EXPECTED_SHA, OEM_ARCHIVE)
    else:
        flash = Path(full_flash) if full_flash else source / 'full_flash_pass1.bin'
        verify_file(flash, FULL_SIZE, FULL_SHA)
        data = flash.read_bytes()[APP_OFFSET:APP_OFFSET + FIRMWARE_SIZE]
        if len(data) != FIRMWARE_SIZE or hashlib.sha256(data).hexdigest() != EXPECTED_SHA:
            raise ValueError('Application V1.21 de référence absente de la capture Flash')
        firmware = cache / FIRMWARE_NAME
        firmware.parent.mkdir(parents=True, exist_ok=True)
        temporary = firmware.with_suffix('.CDD.part')
        temporary.write_bytes(data)
        temporary.replace(firmware)
    for filename, (size, digest) in EXPECTED_FILES.items():
        resolve_input(source, cache, filename, size, digest, NAND_ARCHIVE, nand=True)
    return firmware, cache / 'NAND_ORIGINAUX'


def prepare_sct_reference(source, cache):
    return resolve_input(source, cache, SCT_NAME, SCT_SIZE, SCT_SHA, OEM_ARCHIVE)
