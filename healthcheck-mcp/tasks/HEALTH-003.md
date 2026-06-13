# [DONE][TASKLOG][P0] HEALTH-003 - Implement HTTP endpoint check functionality

**Date:** 2026-03-06
**Workspace:** `D:\Dev\CATMEastrolab\healthcheck-mcp`
**Status:** Completed

## Objective
Реализовать функцию, которая асинхронно проверяет доступность HTTP-эндпоинта.

## Scope
1.  Создание файла `src/http-check.js`.
2.  Использование `axios` для выполнения HTTP GET-запросов.
3.  Функция должна принимать `url`, `timeout` в качестве аргументов.
4.  Функция должна возвращать `Promise`, который разрешается при получении ответа `2xx` и отклоняется в остальных случаях.

## Done Definition
1.  Файл `src/http-check.js` создан.
2.  Функция экспортирована для использования в других модулях.

## Implementation
1.  Создан файл `src/http-check.js`.
2.  Реализована `async` функция `checkHttpEndpoint`, которая использует `axios.get`.
3.  Добавлена проверка статус-кода ответа.
4.  Функция экспортирована через `module.exports`.

## Verification
Модульное тестирование будет реализовано на следующем этапе. На данный момент верификация заключается в корректном создании файла и экспорте функции.

## Artifacts
1. `healthcheck-mcp/src/http-check.js`
