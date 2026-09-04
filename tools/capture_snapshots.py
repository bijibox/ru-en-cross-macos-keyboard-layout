#!/usr/bin/env python3
"""Capture the system's typing/control tables without changing input sources."""
import argparse
import json
import platform
import subprocess
from pathlib import Path

from macos_layout import MacLayouts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='JSON output path for review')
    args = parser.parse_args()
    native = MacLayouts()
    try:
        build = subprocess.check_output(['sw_vers', '-buildVersion'], text=True).strip()
        data = {'source': f'macOS {platform.mac_ver()[0]} ({build}), UCKeyTranslate, key-down, no dead keys',
                'modifiers': [0, 2, 4, 6, 16], 'layouts': {}}
        sources = {sid: native.data(native.find(sid))
                   for sid in ('com.apple.keylayout.US', 'com.apple.keylayout.RussianWin')}

        def maps(source, keyboard_type):
            return [[native.translate(source, key, modifiers, keyboard_type) for key in range(128)]
                    for modifiers in data['modifiers']]

        for sid, source in sources.items():
            data['layouts'][sid] = {shape: maps(source, keyboard_type)
                                    for shape, keyboard_type in (('ANSI', 2), ('ISO', 5), ('JIS', 18))}
        # Canonical hardware IDs used in Apple's uchr resources. UCKeyTranslate
        # normalizes USB types (e.g. 40/41/42) before looking up these ranges.
        ranges = []
        for keyboard_type in list(range(31)) + list(range(192, 208)):
            values = {sid: maps(source, keyboard_type) for sid, source in sources.items()}
            shape = next(shape for shape in ('ISO', 'ANSI', 'JIS')
                         if all(data['layouts'][sid][shape] == value for sid, value in values.items()))
            if ranges and ranges[-1]['last'] == keyboard_type - 1 and ranges[-1]['mapSet'] == shape:
                ranges[-1]['last'] = keyboard_type
            else:
                ranges.append({'first': keyboard_type, 'last': keyboard_type, 'mapSet': shape})
        data['hardware'] = ranges
        args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(args.output)
    finally:
        native.close()


if __name__ == '__main__':
    main()
