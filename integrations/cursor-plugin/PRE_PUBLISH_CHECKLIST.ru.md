# Чеклист до подачи в Cursor Marketplace (PyRTKAI)

Используйте перед отправкой на [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish). Пока репозиторий **не публичный**, отмечайте пункты подготовки; после открытия — замените плейсхолдеры в `plugin.json`.

## Соответствие типичным требованиям ревью

| Пункт | Статус в проекте | Что сделать |
|--------|------------------|-------------|
| Открытый исходник + лицензия | В корне есть **`LICENSE`** (текст MIT), **`pyproject.toml`** и манифест плагина указывают **MIT**. | После публикации репо GitHub должен показывать лицензию; при необходимости включить **Security advisories**. |
| `plugin.json` валиден | Есть `.cursor-plugin/plugin.json`. | Перед submit: **влить** ключи из **`plugin.repository.fragment.json`** (заменить `YOUR_ORG`) — реальные **`repository`** / **`homepage`**. |
| Безопасность | Есть **`SECURITY.md`** (как сообщать о уязвимостях). | После публикации репо проверить доступность **Report a vulnerability** (GitHub). |
| Логотип | Файл **`assets/logo.png`**, в манифесте поле **`logo`**. | При смене файла обновить при необходимости и прогнать тесты (SHA хука не затрагивается). |
| Описание и README | Описание в манифесте + README бандла. | По запросу ревью: краткое «что делает / как установить Python» (см. README про PEP 668). |
| Крючки протестированы локально | CI проверяет манифест, пути, SHA скрипта; хук гоняется с `PYRTKAI_PYTHON`. | **Обязательно вручную:** Cursor + агент + Shell + `pyrtkai doctor --json`. |
| Установка `pyrtkai` у пользователя | Пакет не ставится сам плагином; нужен **venv / pipx / editable**. | Документировано в README бандла и корневом README (PEP 668). Для venv задать **`PYRTKAI_PYTHON`** на интерпретатор с установленным пакетом. |

## Шаблон полей для `plugin.json` (после публикации репозитория)

Подставьте свой org/repo:

```json
"repository": "https://github.com/YOUR_ORG/PyRTKAI",
"homepage": "https://github.com/YOUR_ORG/PyRTKAI#readme",
"logo": "assets/logo.png"
```

Поле `logo` уже можно оставить как в репозитории; `repository` / `homepage` — добавить в JSON **вручную** перед отправкой (не коммитьте чужие URL).

## Ошибка `externally-managed-environment` (Debian/Ubuntu)

Это **PEP 668**: в системный Python нельзя `pip install` без `--break-system-packages`. Рекомендуется:

1. **Приоритет — venv в корне клона + editable (как у разработчиков):**  
   ```bash
   cd /path/to/PyRTKAI
   python3 -m venv .venv
   .venv/bin/pip install -U pip
   .venv/bin/pip install -e .
   ```  
   Для хука Cursor: **`PYRTKAI_PYTHON=/path/to/PyRTKAI/.venv/bin/python`** (лучше абсолютный путь в профиле / сессии, откуда стартует Cursor).

2. **Пакет не на PyPI** — `pip install pyrtkai` пока не сработает; после релиза на PyPI в любом venv достаточно `pip install pyrtkai` (при необходимости всё ещё задайте `PYRTKAI_PYTHON`).

3. **Альтернатива:** отдельный venv, например  
   `python3 -m venv ~/.venvs/pyrtkai && ~/.venvs/pyrtkai/bin/pip install -e /path/to/PyRTKAI`  
   и **`PYRTKAI_PYTHON=$HOME/.venvs/pyrtkai/bin/python`**.

4. **pipx:**  
   `pipx install /path/to/PyRTKAI` или из каталога клона `pipx install .`. После PyPI — `pipx install pyrtkai`.

## Ручная проверка (E2E)

1. Установить `pyrtkai` (приоритет: **`.venv` в клоне** + **`pip install -e .`**).  
2. Прописать/слить `hooks` из `hooks/hooks.json` в `~/.cursor/hooks.json`, скрипт — в согласованный путь.  
3. Задать **`PYRTKAI_PYTHON`** на интерпретатор с пакетом (часто **`…/PyRTKAI/.venv/bin/python`**).  
4. Перезапустить Cursor, вызвать Shell у агента, выполнить **`pyrtkai doctor --json`** → `hooks_json.configured` и `hook_integrity.ok`.

После этого можно подавать заявку и править по замечаниям ревью.
