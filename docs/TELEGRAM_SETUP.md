# Подключение Telegram-бота и Mini App

## 1. Создание бота через @BotFather

1. Откройте Telegram и найдите **@BotFather**.
2. Отправьте `/newbot`, придумайте имя и username (должен заканчиваться на `bot`, например `perekup_sim_bot`).
3. BotFather выдаст токен вида `123456789:AA...`. Это `TELEGRAM_BOT_TOKEN`.
4. Никому не показывайте токен и не коммитьте его в git.

## 2. Настройка Mini App

1. Отправьте @BotFather команду `/newapp`.
2. Выберите вашего бота.
3. Укажите название (например, `Перекуп Симулятор`), описание и обложку.
4. В поле **Web App URL** вставьте HTTPS-адрес фронтенда, например:
   `https://perekup.example.com/`
5. Получите ссылку вида `https://t.me/perekup_sim_bot/app` — по ней открывается игра.

Альтернатива без BotFather UI — кнопка меню:

```
/mybots → ваш бот → Bot Settings → Menu Button → Configure Menu Button
URL: https://perekup.example.com/
Текст: 🚗 Играть
```

## 3. Настройка сервера

В `.env` на сервере:

```env
TELEGRAM_BOT_TOKEN=123456789:AA_ваш_токен
TELEGRAM_DEV_MODE=false
CORS_ORIGINS=https://perekup.example.com
VITE_API_URL=/api
```

Перезапуск:

```bash
docker compose up -d --build
docker compose logs -f backend
```

## 4. Проверка авторизации

1. Откройте Mini App из Telegram (кнопка меню или ссылка `/app`).
2. Backend проверяет подпись `initData` HMAC-SHA256 по схеме Telegram (`WebAppData` + токен бота).
3. Подделать `telegram_id` или баланс на клиенте нельзя — все расчёты на сервере.
4. Проверить логи: `docker compose logs backend | grep -i telegram`.

## 5. Локальная разработка

Для входа без Telegram оставьте `TELEGRAM_DEV_MODE=true` — фронт отправит `initData="dev"` и войдёт как тестовый пользователь. В production всегда `false`.

## 6. (Опционально) Уведомления через бота

MVP не спамит. Если захотите уведомления «появилось предложение» — используйте Bot API `sendMessage` по сохранённому `telegram_id` только после явного согласия игрока (переключатель в профиле).
