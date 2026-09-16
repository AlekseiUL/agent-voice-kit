# Agent Voice Kit — «Голос агента»

[English README](README.md)

[![CI](https://github.com/AlekseiUL/agent-voice-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/AlekseiUL/agent-voice-kit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)

Превращает ответ AI-агента или Markdown-файл в проверенный MP3 либо готовый для Telegram Ogg/Opus. Agent Voice Kit обращается к серверному Microsoft Edge Read Aloud через независимую библиотеку [`edge-tts`](https://github.com/rany2/edge-tts), поэтому нейросетевая модель не запускается на вашем компьютере.

Главная часть проекта — не сам вызов TTS, а надёжная обвязка: ограниченный повтор, короткие фрагменты, продолжение после сбоя, полная проверка аудио и атомарная публикация результата.

## Чем отличается от `edge-tts`

[`edge-tts`](https://github.com/rany2/edge-tts) — upstream-клиент, который обращается к Microsoft Edge Read Aloud. В нём уже есть прямой синтез, список голосов, субтитры и настройки темпа/тона. Agent Voice Kit — **не форк и не замена**: он устанавливает `edge-tts` отдельной зависимостью и добавляет слой надёжности для работы AI-агента.

Agent Voice Kit добавляет очистку Markdown, безопасное деление текста, один ограниченный повтор временной ошибки, продолжение из проверенных фрагментов, полную проверку декодирования, атомарную публикацию, Ogg/Opus для Telegram и JSON-квитанцию. Список голосов, субтитры и воспроизведение upstream не дублируются — для этих задач используйте `edge-tts` напрямую.

## Возможности

- читает UTF-8 Markdown или принимает текст напрямую;
- убирает служебную Markdown-разметку, сохраняя читаемый смысл;
- делит длинный текст по предложениям и словам;
- один раз повторяет запрос после временной ошибки Edge;
- сохраняет каждый проверенный фрагмент и продолжает идентичный запрос;
- создаёт MP3 или совместимый с голосовыми Telegram Ogg/Opus;
- проверяет длительность и полностью декодирует результат через FFmpeg;
- записывает итоговый файл атомарно и защищает от случайной перезаписи;
- возвращает короткий результат или JSON-квитанцию.

## Важное ограничение

Это не официальный Microsoft SDK и не размещённый нами TTS-сервис. Потребительский endpoint Edge Read Aloud не даёт этому проекту SLA и может измениться или перестать работать. Нужен интернет. Не отправляйте чувствительный текст, если его передача внешнему сервису для вас неприемлема.

Если нужны договорные гарантии или коммерческая поддержка, рассмотрите официальный TTS-провайдер. Agent Voice Kit намеренно не переключается на другой сервис без ведома пользователя.

## Требования

- Python 3.10 или новее;
- `ffmpeg` и `ffprobe` в `PATH`;
- интернет для живого синтеза.

Установка FFmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg
```

## Установка

Через `uv`:

```bash
uv tool install "git+https://github.com/AlekseiUL/agent-voice-kit.git@v0.2.1"
agent-voice --version
agent-voice --doctor --json
```

Или из клона:

```bash
git clone https://github.com/AlekseiUL/agent-voice-kit.git
cd agent-voice-kit
uv sync
uv run agent-voice --help
```

`--doctor` работает без сети: проверяет `edge-tts`, FFmpeg/ffprobe, нужные кодировщики и доступ к кэшу, не отправляя текст Microsoft. Доступ к сети подтверждается отдельным коротким синтезом.

## Установка силами AI-агента

Отправьте агенту ссылку на репозиторий и инструкцию:

> Установи Agent Voice Kit и следуй `INSTALL_FOR_AGENTS.md`. Не используй sudo, не меняй мой профиль, не перезапускай сервисы и ничего не отправляй наружу без согласования. Запусти offline doctor и один короткий живой тест, затем покажи доказательства и оставшийся риск.

Полный сценарий для копирования находится в [docs/AGENT_SETUP.md](docs/AGENT_SETUP.md), а закреплённый безопасный контракт — в [INSTALL_FOR_AGENTS.md](INSTALL_FOR_AGENTS.md). CLI подходит любому агенту, который умеет запускать команды; способ нативной доставки зависит от платформы.

Для Hermes Agent после проверки CLI установите поддерживаемый skill:

```bash
hermes skills install \
  https://raw.githubusercontent.com/AlekseiUL/agent-voice-kit/v0.2.1/integrations/hermes/SKILL.md \
  --name agent-voice --yes
```

Затем начните новую сессию или выполните `/reset`. Skill описывает голосовой ответ, полную озвучку Markdown и нативное голосовое вложение Telegram.

## Быстрый старт

Озвучить Markdown-файл для голосового сообщения Telegram:

```bash
agent-voice answer.md --output answer.ogg
```

Озвучить переданный текст:

```bash
agent-voice --text "Агент закончил задачу." --output answer.ogg
```

Сделать речь немного быстрее:

```bash
agent-voice answer.md \
  --voice ru-RU-DmitryNeural \
  --rate=+15% \
  --output answer.ogg
```

Получить машинную квитанцию:

```bash
agent-voice answer.md --output answer.ogg --json
```

Пример сокращённого ответа:

```json
{
  "success": true,
  "output": "answer.ogg",
  "provider": "edge",
  "chunks": 3,
  "resumed_chunks": 3,
  "duration_seconds": 72.4
}
```

Полная квитанция также содержит голос, формат, размер, SHA-256 и идентификатор задания. В ней сохраняется только имя результата, без абсолютного локального пути.

## Ошибки и продолжение

Для каждого нового фрагмента допускаются максимум две попытки: исходный запрос и один повтор после timeout, ошибки соединения, HTTP 429/5xx, `NoAudioReceived` или `WebSocketError`. Ошибки конфигурации и HTTP 403 не повторяются.

Готовый фрагмент попадает в checkpoint только после проверки. Повторный запуск с тем же текстом и настройками использует сохранённые части. Манифест содержит хеши и метаданные аудио, но не исходный текст. Логический срок хранения — семь дней; версия 0.2.1 пока не удаляет просроченные каталоги автоматически.

Отключить checkpoint и повтор для exact-one задачи:

```bash
agent-voice answer.md --output answer.ogg --no-resume
```

## Подключение к агенту

CLI не привязан к конкретной агентной платформе. Агент запускает команду, проверяет код возврата или JSON и передаёт готовый файл через собственный канал доставки:

```python
import subprocess

result = subprocess.run(
    ["agent-voice", "reply.md", "--output", "reply.ogg", "--json"],
    text=True,
    capture_output=True,
    check=True,
)
print(result.stdout)
```

Telegram-бот отправляет полученный `.ogg` своим методом голосовых сообщений. Токены, ID чатов и логика отправки намеренно не входят в этот репозиторий.

## Команды

```text
agent-voice INPUT [-o FILE]
agent-voice --text TEXT [-o FILE]
agent-voice --doctor [--json]
```

Актуальный список параметров выводит `agent-voice --help`.

Безопасные настройки по умолчанию:

- результат должен оканчиваться на `.ogg` или `.mp3`;
- существующий отличный файл не заменяется без `--force`;
- `--force` действует только на явно указанный результат;
- запись через символическую ссылку запрещена;
- одновременный запуск одинаковой записи возвращает понятную ошибку занятости, а не портит checkpoint.

## Разработка

```bash
uv sync --extra dev
uv run pytest
uv run python scripts/privacy_scan.py
uv build
```

Unit-тесты создают локальные тестовые тоны и не обращаются к Microsoft. Живой smoke запускается отдельно:

```bash
uv run agent-voice --text "Проверка живого синтеза." --output /tmp/agent-voice-live.ogg
```

## Атрибуция и лицензии

Код Agent Voice Kit распространяется по [лицензии MIT](LICENSE). `edge-tts` — отдельный проект под LGPL-3.0. FFmpeg — внешняя runtime-зависимость и не включён в репозиторий. Источники, лицензии и границы использования сервиса Microsoft описаны в [NOTICE.md](NOTICE.md).

## Ссылки автора

- GitHub: https://github.com/AlekseiUL
- YouTube: https://youtube.com/@alekseiulianov
- Telegram — Sprut AI: https://t.me/Sprut_AI
- Telegram-сообщество: https://t.me/+eH-qNIDmud8zNDZi
- AI Операционка / поддержка: https://t.me/tribute/app?startapp=sJyg

Проект создан и поддерживается [AlekseiUL](https://github.com/AlekseiUL) вместе с участниками сообщества.
