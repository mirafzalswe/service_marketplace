# Service Marketplace - Документация

## Обзор проекта

Service Marketplace - это веб-приложение на Django REST Framework для управления услугами, заказами и платежами. Система поддерживает три типа пользователей: клиенты, исполнители и администраторы.

## Архитектура системы

### Основные компоненты

- **Django REST Framework** - основной фреймворк для API
- **JWT Authentication** - аутентификация пользователей
- **Django Channels** - WebSocket уведомления в реальном времени
- **SQLite** - база данных (для разработки)
- **Celery** - асинхронные задачи
- **drf-spectacular** - автоматическая генерация документации API

### Структура приложений

```
service_marketplace/
├── accounts/          # Управление пользователями
├── services/          # Каталог услуг
├── orders/           # Управление заказами
├── payments/         # Обработка платежей
└── service_marketplace/  # Основные настройки
```

## Модели данных

### Пользователи (accounts)

#### User (Кастомная модель пользователя)
```python
class User(AbstractUser):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('worker', 'Worker'), 
        ('admin', 'Admin'),
    ]
    role = CharField(choices=ROLE_CHOICES, default='client')
    phone_number = CharField(max_length=15, blank=True)
    date_of_birth = DateField(null=True, blank=True)
    avatar = ImageField(upload_to='avatars/', null=True, blank=True)
```

#### WorkerProfile
```python
class WorkerProfile(Model):
    user = OneToOneField(User, on_delete=CASCADE)
    bio = TextField(blank=True)
    skills = TextField(blank=True)
    hourly_rate = DecimalField(max_digits=8, decimal_places=2, null=True)
    rating = DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = PositiveIntegerField(default=0)
    is_verified = BooleanField(default=False)
```

### Услуги (services)

#### ServiceCategory
```python
class ServiceCategory(Model):
    name = CharField(max_length=100, unique=True)
    description = TextField(blank=True)
    icon = CharField(max_length=50, blank=True)
```

#### Service
```python
class Service(Model):
    name = CharField(max_length=200)
    description = TextField()
    category = ForeignKey(ServiceCategory, on_delete=CASCADE)
    base_price = DecimalField(max_digits=10, decimal_places=2)
    duration_hours = PositiveIntegerField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
```

### Заказы (orders)

#### Order
```python
class Order(Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    
    client = ForeignKey(User, on_delete=CASCADE, related_name='client_orders')
    worker = ForeignKey(User, on_delete=SET_NULL, null=True, related_name='worker_orders')
    service = ForeignKey(Service, on_delete=CASCADE)
    description = TextField()
    address = CharField(max_length=255)
    scheduled_date = DateTimeField()
    quantity = PositiveIntegerField(default=1)
    total_price = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(choices=STATUS_CHOICES, default='pending')
```

#### OrderStatus
```python
class OrderStatus(Model):
    order = ForeignKey(Order, on_delete=CASCADE, related_name='status_history')
    status = CharField(choices=Order.STATUS_CHOICES)
    comment = TextField(blank=True)
    created_by = ForeignKey(User, on_delete=CASCADE)
    created_at = DateTimeField(auto_now_add=True)
```

### Платежи (payments)

#### Payment
```python
class Payment(Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('payme', 'Payme'),
        ('click', 'Click'),
        ('card', 'Credit Card'),
    ]
    
    id = UUIDField(primary_key=True, default=uuid4)
    order = OneToOneField(Order, on_delete=CASCADE)
    user = ForeignKey(User, on_delete=CASCADE)
    amount = DecimalField(max_digits=10, decimal_places=2)
    currency = CharField(max_length=3, default='USD')
    payment_method = CharField(choices=PAYMENT_METHOD_CHOICES)
    status = CharField(choices=PAYMENT_STATUS_CHOICES, default='pending')
    gateway_transaction_id = CharField(max_length=255, blank=True, null=True)
    gateway_response = JSONField(blank=True, null=True)
```

## API Endpoints

### Аутентификация
- `POST /api/auth/register/` - Регистрация пользователя
- `POST /api/auth/login/` - Вход в систему
- `POST /api/auth/refresh/` - Обновление JWT токена
- `POST /api/auth/logout/` - Выход из системы

### Пользователи
- `GET /api/users/` - Список пользователей
- `GET /api/users/{id}/` - Детали пользователя
- `PUT /api/users/{id}/` - Обновление профиля
- `GET /api/workers/` - Список исполнителей
- `GET /api/workers/{id}/` - Профиль исполнителя

### Услуги
- `GET /api/services/categories/` - Категории услуг
- `POST /api/services/categories/` - Создание категории (админ)
- `GET /api/services/` - Список услуг
- `POST /api/services/` - Создание услуги (исполнитель)
- `GET /api/services/{id}/` - Детали услуги
- `PUT /api/services/{id}/` - Обновление услуги

### Заказы
- `GET /api/orders/` - Список заказов
- `POST /api/orders/create/` - Создание заказа (клиент)
- `GET /api/orders/{id}/` - Детали заказа
- `POST /api/orders/{id}/assign/` - Назначение исполнителя
- `POST /api/orders/{id}/status/` - Обновление статуса заказа

### Платежи
- `GET /api/payments/` - Список платежей
- `POST /api/payments/order/{order_id}/pay/` - Создание платежа
- `GET /api/payments/{id}/` - Детали платежа
- `POST /api/payments/{id}/refund/` - Возврат платежа (админ)

## Система разрешений

### Роли пользователей

#### Client (Клиент)
- Создание заказов
- Просмотр своих заказов
- Оплата заказов
- Просмотр каталога услуг

#### Worker (Исполнитель)
- Создание услуг
- Принятие заказов
- Обновление статуса заказов
- Управление профилем исполнителя

#### Admin (Администратор)
- Полный доступ ко всем функциям
- Управление категориями услуг
- Обработка возвратов
- Модерация контента

### Кастомные разрешения

```python
class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.role == 'admin'

class IsWorker(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'worker'

class IsClient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'client'
```

## WebSocket уведомления

Система поддерживает уведомления в реальном времени через WebSocket:

### Подключение
```javascript
const socket = new WebSocket('ws://localhost:8000/ws/notifications/');
```

### Типы уведомлений
- `order_created` - Новый заказ создан
- `order_assigned` - Заказ назначен исполнителю
- `order_status_changed` - Изменен статус заказа
- `payment_success` - Платеж успешно обработан
- `payment_failed` - Ошибка платежа

## Система платежей

### Поддерживаемые методы
- **Payme** - Узбекская платежная система
- **Click** - Узбекская платежная система  
- **Credit Card** - Банковские карты

### Fake Payment Gateway
Для тестирования используется имитация платежного шлюза:

```python
class FakePaymentGateway:
    def process_payment(self, amount, payment_method, card_data=None):
        # Имитация обработки платежа
        success_rate = 0.8  # 80% успешных платежей
        
        if random.random() < success_rate:
            return {
                'status': 'completed',
                'transaction_id': str(uuid.uuid4()),
                'gateway_response': {...}
            }
        else:
            return {
                'status': 'failed',
                'transaction_id': None,
                'gateway_response': {...}
            }
```

## Тестирование

### Структура тестов
```
tests/
├── accounts/tests.py      # Тесты пользователей
├── services/tests.py      # Тесты услуг
├── orders/tests.py        # Тесты заказов
└── payments/tests.py      # Тесты платежей
```

### Запуск тестов
```bash
# Все тесты
pipenv run python manage.py test

# Конкретное приложение
pipenv run python manage.py test accounts

# С подробным выводом
pipenv run python manage.py test --verbosity=2
```

### Покрытие тестами
- **Модели** - тестирование создания и валидации
- **API** - тестирование всех endpoints
- **Разрешения** - проверка доступа по ролям
- **Аутентификация** - JWT токены
- **Платежный шлюз** - мокирование внешних сервисов

## Развертывание

### Требования
```
Python 3.11+
Django 4.2+
PostgreSQL (для продакшена)
Redis (для Celery и Channels)
```

### Установка зависимостей
```bash
# Создание виртуального окружения
pipenv install

# Активация окружения
pipenv shell

# Миграции базы данных
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser
```

### Переменные окружения
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Запуск сервера
```bash
# Django сервер
python manage.py runserver

# Celery worker (в отдельном терминале)
celery -A service_marketplace worker -l info

# Celery beat (планировщик задач)
celery -A service_marketplace beat -l info
```

## API Документация

Автоматическая документация API доступна по адресам:
- **Swagger UI**: `/api/schema/swagger-ui/`
- **ReDoc**: `/api/schema/redoc/`
- **OpenAPI Schema**: `/api/schema/`

## Безопасность

### Реализованные меры
- JWT аутентификация с refresh токенами
- Роль-основанный контроль доступа (RBAC)
- Валидация входных данных
- CORS настройки
- Защита от CSRF атак
- Хеширование паролей (Django по умолчанию)

### Рекомендации для продакшена
- Использование HTTPS
- Настройка файрвола
- Регулярное обновление зависимостей
- Мониторинг логов безопасности
- Резервное копирование базы данных

## Мониторинг и логирование

### Настройка логирования
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'service_marketplace.log',
        },
    },
    'loggers': {
        'payments': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Метрики для мониторинга
- Количество активных пользователей
- Количество заказов по статусам
- Успешность платежей
- Время отклика API
- Ошибки системы

## Roadmap

### Планируемые функции
- [ ] Система отзывов и рейтингов
- [ ] Чат между клиентами и исполнителями
- [ ] Мобильное приложение
- [ ] Интеграция с реальными платежными системами
- [ ] Система скидок и промокодов
- [ ] Аналитика и отчеты
- [ ] Многоязычность
- [ ] Геолокация услуг

### Технические улучшения
- [ ] Кеширование с Redis
- [ ] Оптимизация запросов к БД
- [ ] Контейнеризация с Docker
- [ ] CI/CD pipeline
- [ ] Автоматическое тестирование
- [ ] Мониторинг производительности

## Поддержка

Для получения помощи или сообщения об ошибках:
- Создайте issue в репозитории
- Обратитесь к команде разработки
- Проверьте документацию API

## Лицензия

Этот проект распространяется под лицензией MIT. См. файл LICENSE для подробностей.
