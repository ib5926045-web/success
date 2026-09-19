# Деплой на Ubuntu 24.04

## 0. Требования

- Ubuntu 24.04, 1+ CPU, 2+ ГБ RAM
- Домен с A-записью на IP сервера (например, `perekup.example.com`)
- Открытые порты 80/443

## 1. Установка Docker

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin git
sudo usermod -aG docker $USER
newgrp docker
docker --version && docker compose version
```

## 2. Клонирование и настройка

```bash
git clone <ваш-репозиторий> perekup && cd perekup
cp .env.example .env
nano .env
```

Заполните:

```env
POSTGRES_PASSWORD=<длинный случайный пароль>
SECRET_KEY=<случайная строка 32+ символов>
TELEGRAM_BOT_TOKEN=<токен от @BotFather>
TELEGRAM_DEV_MODE=false
CORS_ORIGINS=https://perekup.example.com
VITE_API_URL=/api
```

Сгенерировать секреты:

```bash
openssl rand -hex 24  # для SECRET_KEY
openssl rand -hex 16  # для POSTGRES_PASSWORD
```

## 3. Первый запуск (HTTP)

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f backend  # дождитесь "Uvicorn running" и "DB ready"
curl http://localhost/api/health
```

## 4. HTTPS через Certbot

Telegram Mini App требует HTTPS.

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d perekup.example.com --agree-tos -m admin@example.com
```

Остановите compose на время выпуска сертификата, если порт 80 занят:

```bash
docker compose stop frontend
sudo certbot certonly --standalone -d perekup.example.com
docker compose start frontend
```

Подключите сертификаты: добавьте в `docker-compose.yml` (сервис frontend):

```yaml
volumes:
  - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
  - /etc/letsencrypt:/etc/letsencrypt:ro
```

И расширьте `nginx/nginx.conf` HTTPS-сервером:

```nginx
server {
    listen 443 ssl;
    server_name perekup.example.com;
    ssl_certificate /etc/letsencrypt/live/perekup.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/perekup.example.com/privkey.pem;
    # ... те же location, что в :80 ...
}
server {
    listen 80;
    server_name perekup.example.com;
    return 301 https://$host$request_uri;
}
```

```bash
docker compose up -d --build
curl https://perekup.example.com/api/health
```

Автообновление сертификатов:

```bash
echo "0 3 * * * root certbot renew --quiet && docker compose -f /root/perekup/docker-compose.yml restart frontend" | sudo tee /etc/cron.d/certbot-renew
```

## 5. Автозапуск

Docker Compose с `restart: unless-stopped` переживает перезагрузку, если включён Docker:

```bash
sudo systemctl enable docker
```

Проверка после ребута:

```bash
docker compose ps
docker compose logs --tail=50 backend
```

## 6. Обслуживание

```bash
# логи
docker compose logs -f backend
docker compose logs -f frontend
# перезапуск
docker compose restart backend
# обновление кода
git pull && docker compose up -d --build
# бэкап базы
docker compose exec db pg_dump -U perekup perekup > backup_$(date +%F).sql
# восстановление
cat backup.sql | docker compose exec -T db psql -U perekup perekup
```

## 7. Проверка готовности

- [ ] `https://ваш-домен/api/health` → `{"ok": true}`
- [ ] Mini App открывается в Telegram по кнопке бота
- [ ] Рынок показывает 5–8 машин
- [ ] Осмотр списывает 30 BYN и раскрывает дефекты
- [ ] Торг меняет цену
- [ ] Покупка → гараж → ремонт → продажа → баланс/опыт/репутация меняются
- [ ] `docker compose logs backend` без ошибок
