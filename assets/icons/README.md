# Иконки ru-en-cross

Ориентир — системные раскладки U.S. и Russian – PC в macOS 26.5.2 (25F84).
В текущем `AppleKeyboardLayouts-L.dat` их основные обозначения — `US` и
кириллическое `РУ`. Здесь они нарисованы системным шрифтом macOS внутри
скруглённого квадрата, с небольшой стрелкой `↔` внизу справа.

Графика строится из контуров CoreText и векторных линий через AppKit.
Стрелка занимает 4 × 2 пункта и не заменяет основное обозначение языка.
Буквы и стрелка прозрачны: для меню используется альфа-маска,
а цвет задаёт macOS через `TISIconIsTemplate` в `Info.plist` бандла.

- `USCrossRussianPC.icns`, `RussianPCCrossUS.icns` — файлы для установки.
- Одноимённые PNG — прозрачные изображения 64 × 64 для просмотра.
- `preview.png` — обзор на светлом и тёмном фоне при разных размерах.

Пересоздать из корня проекта: `make icons`. Генератор находится в
`tools/generate_icons.swift`; ему нужны AppKit, CoreText и Swift из Xcode
или Command Line Tools. Обычная Python-сборка читает готовые ICNS
и не зависит от установленных шрифтов или Swift.

Стандартный способ включения шаблонных значков для клавиатурного бандла
также используется в [Universal Layout](https://github.com/tonsky/Universal-Layout/blob/master/Universal.bundle/Contents/Info.plist).
