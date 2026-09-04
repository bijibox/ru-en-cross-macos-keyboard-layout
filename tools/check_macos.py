#!/usr/bin/env python3
"""Compile a temporary copy with macOS and check actual key translations.

Registers a uniquely identified test bundle in ~/Library/Keyboard Layouts,
without enabling it or selecting it. Removes the test files when done.
"""
import plistlib
import re
import sys
import tempfile
import uuid
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ru_en_cross
from macos_layout import MacLayouts


def main():
    native = MacLayouts()
    install_dir = Path.home() / 'Library' / 'Keyboard Layouts'
    install_dir.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix='ru-en-cross-check-', suffix='.bundle',
                                         dir=install_dir) as temp:
            target = Path(temp)
            files = ru_en_cross.bundle_files()
            info = plistlib.loads(files['Contents/Info.plist'])
            suffix = uuid.uuid4().hex
            info['CFBundleIdentifier'] += '.check' + suffix
            filenames = ('RussianPCCrossUS', 'USCrossRussianPC')
            identifiers = []
            for index, filename in enumerate(filenames):
                entry = info['KLInfo_' + filename]
                entry['TISInputSourceID'] = info['CFBundleIdentifier'] + '.keylayout.' + filename
                identifiers.append(entry['TISInputSourceID'])
                path = f'Contents/Resources/{filename}.keylayout'
                xml = files[path].decode()
                xml = re.sub(r'(<keyboard[^>]* id=")[^"]+',
                             lambda m: m[1] + str(-27001 - index), xml, count=1)
                files[path] = xml.encode()
            files['Contents/Info.plist'] = plistlib.dumps(info)
            ru_en_cross.write_bundle(target, files)
            native.register(target)
            system = {sid: native.data(native.find(sid))
                      for sid in (ru_en_cross.US_SOURCE, ru_en_cross.RUSSIAN_PC_SOURCE)}

            @lru_cache(maxsize=None)
            def expected(source, key, modifiers, keyboard_type):
                value = native.translate(system[source], key, modifiers, keyboard_type)
                if source == ru_en_cross.RUSSIAN_PC_SOURCE and key in (50, 94) and value == 'Ë':
                    return 'Ё'
                return value

            count = 0
            keyboard_types = list(range(31)) + [40, 41, 42, 46, 59] + list(range(192, 208))
            for index, (filename, identifier) in enumerate(zip(filenames, identifiers)):
                source_ref = native.find(identifier)
                languages = native.property(source_ref, 'kTISPropertyInputSourceLanguages')
                language = native.string(native.cf.CFArrayGetValueAtIndex(languages, 0))
                if language != ('ru', 'en')[index]:
                    raise AssertionError(f'{filename}: unexpected language {language!r}')
                name = native.string(native.property(source_ref, 'kTISPropertyLocalizedName'))
                if name != ('Russian – PC cross U.S.', 'U.S. cross Russian – PC')[index]:
                    raise AssertionError(f'{filename}: unexpected display name {name!r}')
                compiled = native.data(source_ref)
                base = (ru_en_cross.RUSSIAN_PC_SOURCE, ru_en_cross.US_SOURCE)[index]
                opposite = (ru_en_cross.US_SOURCE, ru_en_cross.RUSSIAN_PC_SOURCE)[index]
                for keyboard_type in keyboard_types:
                    for flags in range(256):
                        shift = bool(flags & (2 | 32))
                        for key in range(128):
                            if flags & (16 | 128):
                                source, mods = ru_en_cross.US_SOURCE, 16
                            elif flags & 1:
                                source, mods = ru_en_cross.US_SOURCE, 2 if shift else 0
                            elif flags & (8 | 64):
                                source = opposite if key <= 50 or key in (93, 94, 95) else base
                                mods = 2 if shift else 0
                            else:
                                source, mods = base, (2 if shift else 0) | (flags & 4)
                            want = expected(source, key, mods, keyboard_type)
                            got = native.translate(compiled, key, flags, keyboard_type)
                            if got != want:
                                raise AssertionError(f'{filename}: type={keyboard_type}, key={key}, '
                                                     f'modifiers={flags:#x}: {got!r} != {want!r}')
                            count += 1
                print(f'{filename}: macOS compiled the layout; all translations passed')
            print(f'{count:,} native translations checked; temporary bundle removed on exit')
    finally:
        native.close()


if __name__ == '__main__':
    main()
