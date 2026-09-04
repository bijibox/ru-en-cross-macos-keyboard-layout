import itertools
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import ru_en_cross


def parse_layout(text):
    # Expat only supports XML 1.0; Apple accepts C0 character references in
    # keylayout files. Use reversible placeholders while parsing their XML.
    text = re.sub(r'&#x([0-9a-fA-F]+);',
                  lambda m: chr(0xE000 + int(m[1], 16)) if int(m[1], 16) < 32 else m[0], text)
    return ET.fromstring(text)


def output_for(root, code, modifiers=0, shape='ANSI'):
    groups = {'command': 1, 'caps': 4, 'anyShift': 2 | 32,
              'anyOption': 8 | 64, 'anyControl': 16 | 128}
    matches = []
    for select in root.findall('modifierMap/keyMapSelect'):
        for modifier in select:
            allowed = 0
            required_groups = []
            for token in modifier.get('keys').split():
                bits = groups[token.rstrip('?')]
                allowed |= bits
                if not token.endswith('?'):
                    required_groups.append(bits)
            if modifiers & ~allowed == 0 and all(modifiers & bits for bits in required_groups):
                matches.append(int(select.get('mapIndex')))
    if len(matches) != 1:
        raise AssertionError(f'{modifiers:#x} matches {matches}, expected exactly one map')
    key = root.find(f'keyMapSet[@id="{shape}"]/keyMap[@index="{matches[0]}"]/key[@code="{code}"]')
    value = key.get('output')
    return ''.join(chr(ord(c) - 0xE000) if 0xE000 <= ord(c) < 0xE020 else c for c in value)


def tree_bytes(path):
    return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob('*') if p.is_file()}


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        files = ru_en_cross.bundle_files()
        cls.layouts = {name: parse_layout(files[f'Contents/Resources/{name}.keylayout'].decode())
                       for name in ('RussianPCCrossUS', 'USCrossRussianPC')}
        cls.ru = cls.layouts['RussianPCCrossUS']
        cls.us = cls.layouts['USCrossRussianPC']

    def test_basic_language_and_case(self):
        for root, lower, upper in ((self.ru, 'ф', 'Ф'), (self.us, 'a', 'A')):
            for flags, expected in ((0, lower), (2, upper), (32, upper), (4, upper), (6, upper)):
                self.assertEqual(output_for(root, 0, flags), expected)

    def test_option_examples_and_caps_lock(self):
        for option, shift, caps in itertools.product((8, 64, 72), (0, 2, 32, 34), (0, 4)):
            mods = option | shift | caps
            self.assertEqual(output_for(self.ru, 0, mods), 'A' if shift else 'a')
            self.assertEqual(output_for(self.us, 0, mods), 'Ф' if shift else 'ф')
            self.assertEqual(output_for(self.ru, 41, mods), ':' if shift else ';')
            self.assertEqual(output_for(self.ru, 21, mods), '$' if shift else '4')
            self.assertEqual(output_for(self.us, 21, mods), ';' if shift else '4')
            self.assertEqual(output_for(self.us, 18, mods), '!' if shift else '1')

    def test_yo_is_cyrillic_on_ansi_and_iso(self):
        for shape, code in (('ANSI', 50), ('ISO', 10), ('JIS', 93)):
            for flags in (0, 2, 4, 6):
                self.assertEqual(output_for(self.ru, code, flags, shape), 'Ё' if flags else 'ё')
            for flags in (8, 12, 10, 14):
                self.assertEqual(output_for(self.us, code, flags, shape), 'Ё' if flags & 2 else 'ё')
        self.assertEqual(output_for(self.ru, 50, 0, 'ISO'), ']')
        self.assertEqual(output_for(self.us, 93, 0, 'JIS'), '¥')

    def test_command_shortcuts_keep_qwerty_and_shift(self):
        for root in self.layouts.values():
            for option, caps in itertools.product((0, 8, 64, 72), (0, 4)):
                mods = 1 | option | caps
                for code, char in ((0, 'a'), (8, 'c'), (9, 'v'), (6, 'z')):
                    self.assertEqual(output_for(root, code, mods), char)
                    self.assertEqual(output_for(root, code, mods | 2), char.upper())
                self.assertEqual(output_for(root, 33, mods | 32), '{')

    def test_control_shortcuts_with_all_other_modifiers(self):
        for root in self.layouts.values():
            for flags in range(256):
                if flags & (16 | 128):
                    for code, expected in ((0, '\x01'), (8, '\x03'), (2, '\x04'),
                                           (6, '\x1a'), (33, '\x1b'), (30, '\x1d')):
                        self.assertEqual(output_for(root, code, flags), expected)

    def test_every_modifier_combination_is_explicit_and_unambiguous(self):
        for root in self.layouts.values():
            for flags in range(256):
                output_for(root, 0, flags)

    def test_navigation_and_keypad_survive_option(self):
        for root, decimal in ((self.ru, ','), (self.us, '.')):
            for flags in (0, 2, 4, 8, 10, 12, 14, 64, 96):
                for code, expected in ((36, '\r'), (48, '\t'), (49, ' '), (51, '\x08'),
                                       (53, '\x1b'), (117, '\x7f'), (123, '\x1c'),
                                       (124, '\x1d'), (125, '\x1f'), (126, '\x1e'),
                                       (65, decimal), (82, '0')):
                    self.assertEqual(output_for(root, code, flags), expected)

    def test_xml_structure_and_identifiers(self):
        ids = set()
        for root in self.layouts.values():
            self.assertEqual(root.get('group'), '126')
            identifier = int(root.get('id'))
            self.assertTrue(-32768 <= identifier < 0)
            self.assertNotIn(identifier, ids)
            ids.add(identifier)
            ranges = root.findall('layouts/layout')
            covered = set()
            for hardware in ranges:
                values = set(range(int(hardware.get('first')), int(hardware.get('last')) + 1))
                self.assertFalse(values & covered)
                covered |= values
                self.assertIsNotNone(root.find(f'keyMapSet[@id="{hardware.get("mapSet")}"]'))
            self.assertTrue(set(range(31)).issubset(covered))
            for keymap in root.findall('keyMapSet/keyMap'):
                self.assertEqual(sorted(int(k.get('code')) for k in keymap), list(range(128)))
            self.assertFalse(root.findall('.//actions'))


class BuildTests(unittest.TestCase):
    def test_bundle_metadata_uses_resource_filenames(self):
        files = ru_en_cross.bundle_files()
        info = plistlib.loads(files['Contents/Info.plist'])
        source_ids = set()
        for filename in ('RussianPCCrossUS', 'USCrossRussianPC'):
            entry = info['KLInfo_' + filename]
            xml = parse_layout(files[f'Contents/Resources/{filename}.keylayout'].decode())
            self.assertEqual(xml.get('name'), filename)
            source_ids.add(entry['TISInputSourceID'])
            self.assertIn(entry['TISIntendedLanguage'], ('en', 'ru'))
            self.assertTrue(files[f'Contents/Resources/{filename}.icns'].startswith(b'icns'))
        self.assertEqual(len(source_ids), 2)

    def test_build_is_reproducible_and_replaces_stale_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = ru_en_cross.build_bundle(Path(temp))
            first = tree_bytes(target)
            (target / 'stale').write_text('old')
            ru_en_cross.build_bundle(Path(temp))
            self.assertEqual(tree_bytes(target), first)

    def test_build_from_clean_source_copy_without_build_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            checkout = Path(temp)
            shutil.copy2(ROOT / 'ru_en_cross.py', checkout)
            shutil.copytree(ROOT / 'data', checkout / 'data')
            result = subprocess.run([sys.executable, str(checkout / 'ru_en_cross.py'), 'build'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(tree_bytes(checkout / 'build' / ru_en_cross.BUNDLE_NAME),
                             ru_en_cross.bundle_files())

    def test_build_refuses_to_overwrite_reference(self):
        with self.assertRaises(ValueError):
            ru_en_cross.build_bundle(ru_en_cross.ORIGINAL_BUNDLE.parent)

    def test_generation_failure_preserves_previous_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            target = ru_en_cross.build_bundle(Path(temp))
            before = tree_bytes(target)
            with mock.patch.object(ru_en_cross, 'SNAPSHOTS', Path(temp) / 'missing.json'):
                with self.assertRaises(FileNotFoundError):
                    ru_en_cross.build_bundle(Path(temp))
            self.assertEqual(tree_bytes(target), before)

    def test_write_failure_preserves_previous_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            target = ru_en_cross.build_bundle(Path(temp))
            before = tree_bytes(target)
            with mock.patch.object(ru_en_cross, 'write_bundle', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    ru_en_cross.build_bundle(Path(temp))
            self.assertEqual(tree_bytes(target), before)

    def test_install_copies_generated_bundle_and_clean_removes_only_build(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'home'
            build = Path(temp) / 'out'
            with mock.patch.object(Path, 'home', return_value=home):
                target = ru_en_cross.install_bundle(build)
            self.assertEqual(target, home / 'Library/Keyboard Layouts' / ru_en_cross.BUNDLE_NAME)
            self.assertEqual(tree_bytes(target), tree_bytes(build / ru_en_cross.BUNDLE_NAME))
            ru_en_cross.clean(build)
            self.assertFalse((build / ru_en_cross.BUNDLE_NAME).exists())
            self.assertTrue(target.exists())


if __name__ == '__main__':
    unittest.main()
