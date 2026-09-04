# Исходные таблицы

`system_layouts.json` содержит результаты `UCKeyTranslate` для системных
`com.apple.keylayout.US` и `com.apple.keylayout.RussianWin` (`Russian – PC`).
Версия macOS указана в поле `source`. Это исходные данные для сборки;
`build/` можно удалить целиком.

В каждой раскладке есть варианты ANSI, ISO и JIS. Каждый содержит пять
массивов по 128 элементов: без модификаторов, Shift, Caps Lock,
Shift + Caps Lock, Control. Индекс элемента — виртуальный код клавиши.
Пустая строка означает отсутствие вывода. Управляющие символы сохранены
как JSON escapes. `hardware` задаёт диапазоны типов клавиатур для XML.

Снимки сохраняют исходные значения Apple. Исправление латинской `Ë`
на кириллическую `Ё` для ANSI Russian – PC выполняет генератор:
в снимке macOS 26.5.2 верхний регистр клавиш 50 и 94 ошибочно задан U+00CB.

Обновить снимок на macOS для последующего сравнения:

```bash
python3 tools/capture_snapshots.py /tmp/system_layouts.json
```

Команда читает системные раскладки, не переключая текущий источник ввода.
После проверки изменений перенесите новый JSON в `data/system_layouts.json`
и запустите `make test` и `make test-macos`.

Документация API:
[Apple UCKeyTranslate](https://developer.apple.com/documentation/coreservices/1390584-uckeytranslate).
