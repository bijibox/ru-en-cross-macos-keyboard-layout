#!/usr/bin/env python3
"""Small build/install helper for the ru-en-cross keyboard layout bundle."""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from xml.sax.saxutils import quoteattr


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_BUILD_DIR = PROJECT_ROOT / "build"
ORIGINAL_BUNDLE = DEFAULT_BUILD_DIR / "original" / "ru-en-cross.bundle"
SNAPSHOTS = PROJECT_ROOT / "data" / "system_layouts.json"
US_SOURCE = "com.apple.keylayout.US"
RUSSIAN_PC_SOURCE = "com.apple.keylayout.RussianWin"
BUNDLE_NAME = "ru-en-cross.bundle"

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>CFBundleDevelopmentRegion</key>
\t<string>en</string>
\t<key>CFBundlePackageType</key>
\t<string>BNDL</string>
\t<key>CFBundleIdentifier</key>
\t<string>me.elagin.kir.keyboardlayout.ruencross</string>
\t<key>CFBundleName</key>
\t<string>Ru-En Cross Layouts</string>
\t<key>CFBundleVersion</key>
\t<string>2</string>
\t<key>KLInfo_USCrossRussianPC</key>
\t<dict>
\t\t<key>TISInputSourceID</key>
\t\t<string>me.elagin.kir.keyboardlayout.ruencross.keylayout.USCrossRussianPC</string>
\t\t<key>TISIntendedLanguage</key>
\t\t<string>en</string>
\t</dict>
\t<key>KLInfo_RussianPCCrossUS</key>
\t<dict>
\t\t<key>TISInputSourceID</key>
\t\t<string>me.elagin.kir.keyboardlayout.ruencross.keylayout.RussianPCCrossUS</string>
\t\t<key>TISIntendedLanguage</key>
\t\t<string>ru</string>
\t</dict>
</dict>
</plist>
"""

VERSION_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>ProjectName</key>
\t<string>Ru-En Cross Layouts</string>
\t<key>SourceVersion</key>
\t<string>2</string>
\t<key>BuildVersion</key>
\t<string>2</string>
</dict>
</plist>
"""

INFO_PLIST_STRINGS = '''"USCrossRussianPC" = "U.S. cross Russian – PC";
"RussianPCCrossUS" = "Russian – PC cross U.S.";
'''

ICONS_B64 = {
    "RussianPCCrossUS.icns": (
        "aWNucwAACDZpYzA1AAADo0FSR0KDAJH/hgCX/4IAmf+AAJv/AQAAm/8BAACb/wAA////////"
        "///1/wAAm/8BAACb/wEAAJv/gACZ/4IAl/+GAJH/gwCDAJF+hgCXfoIAmX6AAJt+AQAAm34B"
        "AACbfgAA4n6F/4F+Af//g34B//+HfoX/gX4B//+DfgH//4d+Af//g34F//9+fv//g34B//+H"
        "fgH//4N+Bf//fn7//4N+Af//h34B//+DfgH//4F+Bf//fn7//4l+Af//g34B//+BfgX//35+"
        "//+JfoX/hX4B//+LfoX/hX4B//+LfgH//4t+Af//i34B//+LfgH//4t+Af//i34B//+LfgH/"
        "/4t+Af//i34B//+LfgH//4t+Af//i34C/01NgX4BTU2WfgVNTX5+TU2YfoFNmn4BTU2CfgAA"
        "lH6BTYB+AQAAk34JTU1+fk1Nfn4AAJJ+AU1NgX4CTU1+gACZfoIAl36GAJF+gwCDAJF+hgCX"
        "foIAmX6AAJt+AQAAm34BAACbfgAA4n6F/4F+Af//g34B//+HfoX/gX4B//+DfgH//4d+Af//"
        "g34F//9+fv//g34B//+HfgH//4N+Bf//fn7//4N+Af//h34B//+DfgH//4F+Bf//fn7//4l+"
        "Af//g34B//+BfgX//35+//+JfoX/hX4B//+LfoX/hX4B//+LfgH//4t+Af//i34B//+LfgH/"
        "/4t+Af//i34B//+LfgH//4t+Af//i34B//+LfgH//4t+Af//i34C/5SUgX4BlJSWfgWUlH5+"
        "lJSYfoGUmn4BlJSCfgAAlH6BlIB+AQAAk34JlJR+fpSUfn4AAJJ+AZSUgX4ClJR+gACZfoIA"
        "l36GAJF+gwCDAJF+hgCXfoIAmX6AAJt+AQAAm34BAACbfgAA4n6F/4F+Af//g34B//+HfoX/"
        "gX4B//+DfgH//4d+Af//g34F//9+fv//g34B//+HfgH//4N+Bf//fn7//4N+Af//h34B//+D"
        "fgH//4F+Bf//fn7//4l+Af//g34B//+BfgX//35+//+JfoX/hX4B//+LfoX/hX4B//+LfgH/"
        "/4t+Af//i34B//+LfgH//4t+Af//i34B//+LfgH//4t+Af//i34B//+LfgH//4t+Af//i36A"
        "/4F+Af//ln4F//9+fv//mH6B/5p+Af//gn4AAJR+gf+AfgEAAJN+Cf//fn7//35+AACSfgH/"
        "/4F+Av//foAAmX6CAJd+hgCRfoMAaWMxMQAAAbGJUE5HDQoaCgAAAA1JSERSAAAAIAAAACAI"
        "BgAAAHN6evQAAAABc1JHQgCuzhzpAAAARGVYSWZNTQAqAAAACAABh2kABAAAAAEAAAAaAAAA"
        "AAADoAEAAwAAAAEAAQAAoAIABAAAAAEAAAAgoAMABAAAAAEAAAAgAAAAAKyGYvMAAAETSURB"
        "VFgJ7ZfhDYIwEIXBOIN7uIgjQWAH53IPl9A8yUeOUpA0tEeM/dO7157v3UMK1NXCaJrmtbCU"
        "BPd9X8cKJ+DepDFCYVbMKKAUOaIQ8RFQmtyKOJF4ze4Cai/7cdzdAXcBZ6ywc9d1Np3FbdtO"
        "MPaHOJvW1o/pAMpTOqJ263xsB7Z2gVPhtQ7z2O+5OxA9iFAeUyyMjpfWqf+2T/XuDkTPATrb"
        "0gF7U2d3B/4CfteB272qHpf5Q02YxaPnQOo/OqyD6Pocnp5hrv1ZBYgAUsUaiBmyAgeRJbQx"
        "ArK/lq85oG+DrHcB5Oqc7sFwIJsAiCAWITFrwj6XQEHp1/PJp5kEaJQSAbk4RweU2LG3GEtq"
        "ed79UmbhbYGM/gAAAABJRU5ErkJggmljMDQAAAGcQVJHQoAAh/+BAIv/AQAAi/8AAP//m/8A"
        "AIv/AQAAi/+BAIf/gACAAId+gQCLfgEAAIt+AACPfoH/An5+/4B+AP+CfgD/gH4C/37/gH4A"
        "/4J+AP+AfgX/fn7/fv+DfoH/gX4A/4R+AP+EfgD/hH4A/4R+AP+EfgD/hH4A/41+A01+fk2K"
        "fgRNTX5+AIh+BE1NfgAAh34DTX5+TYEAh36AAIAAh36BAIt+AQAAi34AAI9+gf8Cfn7/gH4A"
        "/4J+AP+AfgL/fv+AfgD/gn4A/4B+Bf9+fv9+/4N+gf+BfgD/hH4A/4R+AP+EfgD/hH4A/4R+"
        "AP+EfgD/jX4DlH5+lIp+BJSUfn4AiH4ElJR+AACHfgOUfn6UgQCHfoAAgACHfoEAi34BAACL"
        "fgAAj36B/wJ+fv+AfgD/gn4A/4B+Av9+/4B+AP+CfgD/gH4F/35+/37/g36B/4F+AP+EfgD/"
        "hH4A/4R+AP+EfgD/hH4A/4R+AP+NfgP/fn7/in4E//9+fgCIfgT//34AAId+A/9+fv+BAId+"
        "gABpbmZvAAABPmJwbGlzdDAw1AECAwQFBgcKWCR2ZXJzaW9uWSRhcmNoaXZlclQkdG9wWCRv"
        "YmplY3RzEgABhqBfEA9OU0tleWVkQXJjaGl2ZXLRCAlUcm9vdIABpwsMFxgZGh5VJG51bGzT"
        "DQ4PEBMWV05TLmtleXNaTlMub2JqZWN0c1YkY2xhc3OiERKAAoADohQVgASABYAGVG5hbWVf"
        "EBZhc3NldGNhdGFsb2ctcmVmZXJlbmNlVGljb27TDQ4PGxwWoKCABtIfICEiWiRjbGFzc25h"
        "bWVYJGNsYXNzZXNcTlNEaWN0aW9uYXJ5oiEjWE5TT2JqZWN0CBEaJCkyN0lMUVNbYWhwe4KF"
        "h4mMjpCSl7C1vL2+wMXQ2ebpAAAAAAAAAQEAAAAAAAAAJAAAAAAAAAAAAAAAAAAAAPI="
    ),
    "USCrossRussianPC.icns": (
        "aWNucwAABxBpYzA1AAAC5UFSR0KDAJH/hgCX/4IAmf+AAJv/AQAAm/8BAACb/wAA////////"
        "///1/wAAm/8BAACb/wEAAJv/gACZ/4IAl/+GAJH/gwCDAJF+hgCXfoIAmX6AAJt+AQAAm34B"
        "AACbfgAA6n6D/5d+g/+VfgH//4N+Af//k34B//+DfgH//5N+Af//g34B//+TfgH//4N+Af//"
        "k36H/5N+h/+TfgH//4N+Af//k34B//+DfgH//5N+Af//g34B//+TfgH//4N+Af//k34B//+D"
        "fgH//5N+Af//g34E//9+TU2BfgFNTZZ+BU1Nfn5NTZh+gU2afgFNTYJ+AACUfoFNgH4BAACT"
        "fglNTX5+TU1+fgAAkn4BTU2BfgJNTX6AAJl+ggCXfoYAkX6DAIMAkX6GAJd+ggCZfoAAm34B"
        "AACbfgEAAJt+AADqfoP/l36D/5V+Af//g34B//+TfgH//4N+Af//k34B//+DfgH//5N+Af//"
        "g34B//+Tfof/k36H/5N+Af//g34B//+TfgH//4N+Af//k34B//+DfgH//5N+Af//g34B//+T"
        "fgH//4N+Af//k34B//+DfgT//36UlIF+AZSUln4FlJR+fpSUmH6BlJp+AZSUgn4AAJR+gZSA"
        "fgEAAJN+CZSUfn6UlH5+AACSfgGUlIF+ApSUfoAAmX6CAJd+hgCRfoMAgwCRfoYAl36CAJl+"
        "gACbfgEAAJt+AQAAm34AAOp+g/+XfoP/"
        "lX4B//+DfgH//5N+Af//g34B//+TfgH//4N+Af//k34B//+DfgH//5N+h/+Tfof/k34B//+D"
        "fgH//5N+Af//g34B//+TfgH//4N+Af//k34B//+DfgH//5N+Af//g34B//+TfgH//4N+"
        "BP//fv//gX4B"
        "//+WfgX//35+//+YfoH/mn4B//+CfgAAlH6B/4B+AQAAk34J//9+fv//fn4AAJJ+Af//gX4C"
        "//9+gACZfoIAl36GAJF+gwBpYzExAAABjolQTkcNChoKAAAADUlIRFIAAAAgAAAAIAgGAAAA"
        "c3p69AAAAAFzUkdCAK7OHOkAAABEZVhJZk1NACoAAAAIAAGHaQAEAAAAAQAAABoAAAAAAAOg"
        "AQADAAAAAQABAACgAgAEAAAAAQAAACCgAwAEAAAAAQAAACAAAAAArIZi8wAAAPBJREFUWAnt"
        "lwEKwyAQBLX0Df1HP6joB/uPfqJlEzZcRCMNOY+UHJTo2rJza0OMd40KIXwaS7vknLOv/XAl"
        "Hm1aM4QmYRaAUeaEIsQEMNpcQtw4sbqaA3ir+Jm4eQLmAHdG8cs1pVT9eoyxqm+J50qAnbc6"
        "7a3XkjBP4AI49C6o7XFPM9+CXQn07oJe13LdPIEL4H8TeD2Sw6esUlc9kBDg+Z6fkuUccKoA"
        "MKApxijCzDPn1P8D0lCOCaB+LN9KAO8GqgnQHJ2ze2pMQA2ARjSGIcdcgzZtAQajj+erVzMA"
        "oEZB0ByeSwKYyDoaRppKny8lLFX4rjaaDQAAAABJRU5ErkJggmljMDQAAAFXQVJHQoAAh/+B"
        "AIv/AQAAi/8AAP//m/8AAIv/AQAAi/+BAIf/gACAAId+gQCLfgEAAIt+AACTfoD/iX4A/4B+"
        "AP+IfgD/gH4A/4h+gv+IfgD/gH4A/4h+AP+AfgD/iH4A/4B+AP+OfgNNfn5Nin4ETU1+fgCI"
        "fgRNTX4AAId+A01+fk2BAId+gACAAId+gQCLfgEAAIt+AACTfoD/iX4A/4B+AP+IfgD/gH4A"
        "/4h+gv+IfgD/gH4A/4h+AP+AfgD/iH4A/4B+AP+OfgOUfn6Uin4ElJR+fgCIfgSUlH4AAId+"
        "A5R+fpSBAId+gACAAId+gQCLfgEAAIt+AACTfoD/iX4A/4B+AP+IfgD/gH4A/4h+gv+IfgD/"
        "gH4A/4h+AP+AfgD/iH4A/4B+AP+OfgP/fn7/in4E//9+fgCIfgT//34AAId+A/9+fv+BAId+"
        "gABpbmZvAAABPmJwbGlzdDAw1AECAwQFBgcKWCR2ZXJzaW9uWSRhcmNoaXZlclQkdG9wWCRv"
        "YmplY3RzEgABhqBfEA9OU0tleWVkQXJjaGl2ZXLRCAlUcm9vdIABpwsMFxgZGh5VJG51bGzT"
        "DQ4PEBMWV05TLmtleXNaTlMub2JqZWN0c1YkY2xhc3OiERKAAoADohQVgASABYAGVG5hbWVf"
        "EBZhc3NldGNhdGFsb2ctcmVmZXJlbmNlVGljb27TDQ4PGxwWoKCABtIfICEiWiRjbGFzc25h"
        "bWVYJGNsYXNzZXNcTlNEaWN0aW9uYXJ5oiEjWE5TT2JqZWN0CBEaJCkyN0lMUVNbYWhwe4KF"
        "h4mMjpCSl7C1vL2+wMXQ2ebpAAAAAAAAAQEAAAAAAAAAJAAAAAAAAAAAAAAAAAAAAPI="
    ),
}

CROSS_MODIFIER_MAP = """<modifierMap id="Mods" defaultIndex="0">
  <keyMapSelect mapIndex="0">
    <modifier keys=""/>
  </keyMapSelect>
  <keyMapSelect mapIndex="1">
    <modifier keys="anyShift"/>
  </keyMapSelect>
  <keyMapSelect mapIndex="2">
    <modifier keys="caps"/>
  </keyMapSelect>
  <keyMapSelect mapIndex="3">
    <modifier keys="caps anyShift"/>
  </keyMapSelect>
  <keyMapSelect mapIndex="4">
    <modifier keys="anyOption caps?"/>
  </keyMapSelect>
  <keyMapSelect mapIndex="5">
    <modifier keys="anyShift anyOption caps?"/>
  </keyMapSelect>
  <keyMapSelect mapIndex="6">
    <modifier keys="command anyOption? caps?"/>
  </keyMapSelect>
  <keyMapSelect mapIndex="7">
    <modifier keys="command anyShift anyOption? caps?"/>
  </keyMapSelect>
  <keyMapSelect mapIndex="8">
    <modifier keys="anyControl command? anyShift? anyOption? caps?"/>
  </keyMapSelect>
</modifierMap>"""


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def load_snapshots() -> dict:
    data = json.loads(SNAPSHOTS.read_text(encoding="utf-8"))
    if data["modifiers"] != [0, 2, 4, 6, 16]:
        raise ValueError("unexpected snapshot modifier order")
    for source in (US_SOURCE, RUSSIAN_PC_SOURCE):
        for shape in ("ANSI", "ISO", "JIS"):
            maps = data["layouts"][source][shape]
            if len(maps) != 5 or any(len(keys) != 128 for keys in maps):
                raise ValueError(f"incomplete snapshot: {source}/{shape}")
            if any(not isinstance(value, str) or len(value) > 1
                   for keys in maps for value in keys):
                raise ValueError(f"unexpected output: {source}/{shape}")
    return data


def language_maps(data: dict, source: str, shape: str) -> List[List[str]]:
    maps = [keys.copy() for keys in data["layouts"][source][shape]]
    if source == RUSSIAN_PC_SOURCE and shape == "ANSI":
        # Apple's ANSI Russian-PC table has Latin Ë (U+00CB) on these
        # keys. Keep the lower/upper pair in the same Cyrillic alphabet.
        for index in (1, 2, 3):
            for code in (50, 94):
                if maps[index][code] == "Ë":
                    maps[index][code] = "Ё"
    return maps


def render_keymap(index: int, keys: List[str]) -> str:
    lines = [f'  <keyMap index="{index}">']
    for code, value in enumerate(keys):
        # Use Apple's keylayout character references for C0 controls,
        # including its NUL extension; never write literal control bytes.
        output = "".join(f"&#x{ord(char):04x};" for char in value)
        lines.append(f'    <key code="{code}" output="{output}"/>')
    lines.append("  </keyMap>")
    return "\n".join(lines)


def generate_cross_keylayout(
    base_source: str,
    option_source: str,
    group: str,
    layout_id: str,
    name: str,
) -> str:
    data = load_snapshots()
    lines = [
        '<?xml version="1.1" encoding="UTF-8"?>',
        '<!DOCTYPE keyboard SYSTEM "file://localhost/System/Library/DTDs/KeyboardLayout.dtd">',
        '<keyboard group="{0}" id="{1}" name={2} maxout="1">'.format(
            group,
            layout_id,
            quoteattr(name),
        ),
        "<layouts>",
    ]
    for hardware in data["hardware"]:
        lines.append('<layout first="{first}" last="{last}" '
                     'mapSet="{mapSet}" modifiers="Mods"/>'.format(**hardware))
    lines.extend(["</layouts>", CROSS_MODIFIER_MAP])
    for shape in ("ANSI", "ISO", "JIS"):
        base = language_maps(data, base_source, shape)
        opposite = language_maps(data, option_source, shape)
        us = language_maps(data, US_SOURCE, shape)
        maps = base[:4]
        for shift in (0, 1):
            keys = base[shift].copy()
            # Cross only the typing block, including the extra ISO/JIS keys.
            for code in (*range(51), 93, 94, 95):
                keys[code] = opposite[shift][code]
            maps.append(keys)
        # Command shortcuts use QWERTY even with Option/Caps Lock held.
        # Control always produces the system's ASCII control characters.
        maps.extend([us[0], us[1], us[4]])
        lines.append(f'<keyMapSet id="{shape}">')
        lines.extend(render_keymap(index, keys) for index, keys in enumerate(maps))
        lines.append("</keyMapSet>")
    lines.append("</keyboard>")
    return "\n".join(lines) + "\n"


def bundle_files() -> Dict[str, bytes]:
    return {
        "Contents/Info.plist": INFO_PLIST.encode("utf-8"),
        "Contents/version.plist": VERSION_PLIST.encode("utf-8"),
        "Contents/Resources/en.lproj/InfoPlist.strings": INFO_PLIST_STRINGS.encode("utf-16"),
        "Contents/Resources/RussianPCCrossUS.keylayout": generate_cross_keylayout(
            RUSSIAN_PC_SOURCE,
            US_SOURCE,
            "126",
            "-19102",
            "RussianPCCrossUS",
        ).encode("utf-8"),
        "Contents/Resources/USCrossRussianPC.keylayout": generate_cross_keylayout(
            US_SOURCE,
            RUSSIAN_PC_SOURCE,
            "126",
            "-19101",
            "USCrossRussianPC",
        ).encode("utf-8"),
        "Contents/Resources/RussianPCCrossUS.icns": base64.b64decode(
            ICONS_B64["RussianPCCrossUS.icns"]
        ),
        "Contents/Resources/USCrossRussianPC.icns": base64.b64decode(
            ICONS_B64["USCrossRussianPC.icns"]
        ),
    }


def write_bundle(target: Path, files: Dict[str, bytes]) -> None:
    for relative_path, content in files.items():
        path = target / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def replace_bundle(target: Path, files: Dict[str, bytes]) -> None:
    """Stage all files before replacing an existing build or installation."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".ru-en-cross-", dir=target.parent) as temp:
        staged = Path(temp) / BUNDLE_NAME
        write_bundle(staged, files)
        backup = Path(temp) / "previous.bundle"
        had_target = target.exists() or target.is_symlink()
        if had_target:
            target.rename(backup)
        try:
            staged.rename(target)
        except OSError:
            if had_target:
                backup.rename(target)
            raise


def build_bundle(output_dir: Path = DEFAULT_BUILD_DIR) -> Path:
    """Create the installable bundle from source snapshots and embedded assets."""
    output_dir = output_dir.expanduser().resolve()
    target = output_dir / BUNDLE_NAME

    original = ORIGINAL_BUNDLE.resolve()
    if target == original or original in target.parents:
        raise ValueError("output bundle must not overwrite the reference bundle")

    replace_bundle(target, bundle_files())
    return target


def install_bundle(output_dir: Path = DEFAULT_BUILD_DIR) -> Path:
    bundle = build_bundle(output_dir)
    install_dir = Path.home() / "Library" / "Keyboard Layouts"
    target = install_dir / BUNDLE_NAME

    files = {str(path.relative_to(bundle)): path.read_bytes()
             for path in bundle.rglob("*") if path.is_file()}
    replace_bundle(target, files)
    return target


def clean(output_dir: Path = DEFAULT_BUILD_DIR) -> Path:
    output_dir = output_dir.expanduser().resolve()
    target = output_dir / BUNDLE_NAME
    remove_path(target)
    return target


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ru_en_cross.py",
        description="Build and install the ru-en-cross macOS keyboard layout bundle.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    build = subcommands.add_parser("build", help="create build/ru-en-cross.bundle")
    build.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help="directory for the generated bundle (default: build)",
    )

    install = subcommands.add_parser(
        "install",
        help="build and install the bundle into ~/Library/Keyboard Layouts",
    )
    install.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help="temporary build directory (default: build)",
    )

    clean_command = subcommands.add_parser("clean", help="remove the generated bundle")
    clean_command.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help="directory containing the generated bundle (default: build)",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = make_parser().parse_args(argv)

    try:
        if args.command == "build":
            path = build_bundle(args.output_dir)
            print(path)
        elif args.command == "install":
            path = install_bundle(args.output_dir)
            print(path)
        elif args.command == "clean":
            path = clean(args.output_dir)
            print(path)
        else:
            raise ValueError(f"unknown command: {args.command}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
