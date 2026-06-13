# [DONE][TASKLOG][P0] HEALTH-004 - Create MCP server wrapper

**Date:** 2026-03-06
**Workspace:** `D:\Dev\CATMEastrolab\healthcheck-mcp`
**Status:** Completed

## Objective
Обернуть реализованные функции проверки в MCP-совместимый `stdio`-сервер.

## Scope
1.  Создание файла `src/index.js`.
2.  Реализация чтения и парсинга JSON из `stdin`.
3.  Определение MCP-схемы с одним инструментом `wait_for`.
4.  Логика, которая в зависимости от параметра `type` (`tcp` или `http`) вызывает соответствующую функцию проверки.
5.  Вывод результата (успех или ошибка) в `stdout` в формате, совместимом с MCP.

## Done Definition
1.  Файл `src/index.js` создан.
2.  Сервер корректно обрабатывает MCP-запросы из `stdin`.
3.  Сервер успешно вызывает `checkTcpPort` для `type: "tcp"`.
4.  Сервер успешно вызывает `checkHttpEndpoint` для `type: "http"`.

## Implementation
1.  Создан `src/index.js`.
2.  Импортированы функции `checkTcpPort` и `checkHttpEndpoint`.
3.  Определена `MCP_SCHEMA` с инструментом `wait_for`.
4.  Реализована функция `handleRequest` для обработки вызова инструмента, включая логику повторных попыток (`retries`).
5.  Реализована `main` функция, которая читает `stdin`, парсит JSON и вызывает `handleRequest` или отдает схему по запросу `mcp_action: "describe"`.

## Verification
Тестирование будет произведено путем интеграции с `mcporter`.

## Artifacts
1. `healthcheck-mcp/src/index.js`
