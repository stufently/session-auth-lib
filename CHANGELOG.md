# Changelog

## Unreleased

- **Supply-chain: `pypa/gh-action-pypi-publish` запинен по commit-SHA.** В
  `publish.yml` шаг публикации ссылался на `@release/v1` — ПЛАВАЮЩУЮ ветку
  апстрима: любой её коммит автоматически получал бы наш OIDC-токен на аплоад в
  PyPI (пакет `tdata-session-exporter` — транзитивная зависимость userbot'а и
  автоответчиков). Теперь `@ba38be9e461d3875417946c167d0b5f3d385a247` — это
  ровно тот коммит, на который `release/v1` указывала на 2026-07-25, и он же
  является релизом `v1.14.1`, т.е. поведение публикации не меняется.
  Обновлять осознанно: сверить upstream release notes → поменять SHA и
  комментарий с версией. Версия пакета намеренно НЕ бампалась — правка не релиз.

## 0.2.1 — 2026-07-18

- Зависимость `opentele-ng` теперь ставится с PyPI (`opentele-ng>=1.3.1`)
  вместо прямого git-URL — PyPI не принимает пакеты с git-зависимостями.
- Автопубликация на PyPI: `.github/workflows/publish.yml` (тег `v*` → тест →
  сборка → PyPI Trusted Publishing OIDC, environment `pypi`, сверка
  «тег == версия pyproject») и `.github/workflows/autotag.yml` (push в main с
  изменением pyproject.toml → гейт «версия уже на PyPI?» → создание тега →
  dispatch publish).
- Удалён избыточный `setup.py` (дублировал метаданные `pyproject.toml`,
  включая устаревшую git-зависимость).
- README: установка через `pip install tdata-session-exporter`, описан
  релизный процесс (бамп версии → авторелиз).
- По Codex-ревью: строгая сверка «тег == v<версия>» (без стрип-суффиксов),
  добавлен файл `LICENSE` (MIT), в `.gitignore` — стандартные
  Python-исключения (`__pycache__`, `dist/` и т.п.).

## 0.2.0

- Бандл JSON + `.session`, экспорт из tdata, обязательная проверка прокси
  (исторический релиз до ведения changelog).
