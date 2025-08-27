# Service Marketplace API Documentation

## Обзор проекта

**Service Marketplace** - это платформа для предоставления услуг, где клиенты могут заказывать услуги, а работники могут их выполнять.

### Архитектура

- **Backend**: Django REST Framework
- **Authentication**: JWT (JSON Web Tokens)
- **Real-time**: Django Channels (WebSocket)
- **Database**: SQLite (для разработки)
- **API Documentation**: Swagger/OpenAPI 3.0

### Основные компоненты

1. **Accounts** - Управление пользователями и профилями работников
2. **Services** - Каталог услуг и категорий
3. **Orders** - Система заказов и их статусов
4. **Payments** - Обработка платежей

## Модели данных

### User (Пользователь)
```python
- id: UUID (Primary Key)
- username: String (Unique)
- email: String (Unique)
- first_name: String
- last_name: String
- role: Choice ['client', 'worker', 'admin']
- phone: String (Optional)
- avatar: ImageField (Optional)
- is_verified: Boolean
- created_at: DateTime
- updated_at: DateTime
```

### WorkerProfile (Профиль работника)
```python
- user: OneToOne -> User
- specializations: ManyToMany -> Service
- experience_years: Integer
- hourly_rate: Decimal
- rating: Decimal
- is_available: Boolean
- bio: Text
- created_at: DateTime
- updated_at: DateTime
```

### ServiceCategory (Категория услуг)
```python
- name: String (Unique)
- description: Text
- icon: String (Font Awesome class)
```

### Service (Услуга)
```python
- name: String
- description: Text
- category: ForeignKey -> ServiceCategory
- base_price: Decimal
- duration_hours: Integer
- is_active: Boolean
- created_at: DateTime
```

### Order (Заказ)
```python
- client: ForeignKey -> User
- worker: ForeignKey -> User (Optional)
- service: ForeignKey -> Service
- description: Text
- address: String
- scheduled_date: DateTime
- quantity: Integer
- total_price: Decimal
- status: Choice ['pending', 'paid', 'in_progress', 'completed', 'canceled']
- created_at: DateTime
- updated_at: DateTime
- completed_at: DateTime (Optional)
```

### Payment (Платеж)
```python
- id: UUID (Primary Key)
- order: OneToOne -> Order
- user: ForeignKey -> User
- amount: Decimal
- currency: String
- payment_method: Choice ['payme', 'click', 'card']
- status: Choice ['pending', 'processing', 'completed', 'failed', 'canceled', 'refunded']
- gateway_transaction_id: String (Optional)
- gateway_response: JSON (Optional)
- created_at: DateTime
- updated_at: DateTime
- processed_at: DateTime (Optional)
```

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Регистрация пользователя | No |
| POST | `/api/auth/login/` | Авторизация | No |
| POST | `/api/auth/token/refresh/` | Обновление токена | No |

### Users

| Method | Endpoint | Description | Auth Required | Permissions |
|--------|----------|-------------|---------------|-------------|
| GET | `/api/auth/users/` | Список пользователей | Yes | Admin |
| GET | `/api/auth/users/{id}/` | Детали пользователя | Yes | Owner/Admin |
| PUT | `/api/auth/users/{id}/` | Обновление пользователя | Yes | Owner/Admin |
| PATCH | `/api/auth/users/{id}/` | Частичное обновление | Yes | Owner/Admin |

### Worker Profiles

| Method | Endpoint | Description | Auth Required | Permissions |
|--------|----------|-------------|---------------|-------------|
| GET | `/api/auth/worker-profile/` | Профиль работника | Yes | Worker |
| PUT | `/api/auth/worker-profile/` | Обновление профиля | Yes | Worker |
| PATCH | `/api/auth/worker-profile/` | Частичное обновление | Yes | Worker |

### Services

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/services/categories/` | Список категорий | No |
| POST | `/api/services/categories/` | Создание категории | Yes |
| GET | `/api/services/` | Список услуг | No |
| POST | `/api/services/` | Создание услуги | Yes |
| GET | `/api/services/{id}/` | Детали услуги | No |
| PUT | `/api/services/{id}/` | Обновление услуги | Yes |
| PATCH | `/api/services/{id}/` | Частичное обновление | Yes |
| DELETE | `/api/services/{id}/` | Удаление услуги | Yes |

### Orders

| Method | Endpoint | Description | Auth Required | Permissions |
|--------|----------|-------------|---------------|-------------|
| GET | `/api/orders/` | Список заказов | Yes | Based on role |
| POST | `/api/orders/` | Создание заказа | Yes | Client |
| GET | `/api/orders/{id}/` | Детали заказа | Yes | Related users |
| PUT | `/api/orders/{id}/` | Обновление заказа | Yes | Related users |
| PATCH | `/api/orders/{id}/` | Частичное обновление | Yes | Related users |
| POST | `/api/orders/{id}/status/` | Обновление статуса | Yes | Related users |
| POST | `/api/orders/{id}/assign/` | Назначение работника | Yes | Worker |

### Payments

| Method | Endpoint | Description | Auth Required | Permissions |
|--------|----------|-------------|---------------|-------------|
| GET | `/api/payments/` | Список платежей | Yes | Owner/Admin |
| POST | `/api/payments/{order_id}/` | Создание платежа | Yes | Client |
| GET | `/api/payments/{id}/` | Детали платежа | Yes | Owner/Admin |
| POST | `/api/payments/{id}/refund/` | Возврат платежа | Yes | Owner/Admin |

## Роли и разрешения

### Client (Клиент)
- Создание заказов
- Просмотр своих заказов
- Оплата заказов
- Обновление статуса заказа

### Worker (Работник)
- Просмотр доступных заказов
- Назначение себя на заказы
- Обновление статуса заказов
- Управление профилем работника

### Admin (Администратор)
- Полный доступ ко всем ресурсам
- Управление пользователями
- Управление услугами и категориями
- Просмотр всех заказов и платежей

## WebSocket Events

### Подключение
```javascript
const socket = new WebSocket('ws://localhost:8000/ws/orders/');
```

### События

#### Order Events
- `order_created` - Новый заказ создан
- `order_status_updated` - Статус заказа обновлен
- `worker_assigned` - Работник назначен на заказ

#### Payment Events
- `payment_success` - Платеж успешен
- `payment_failed` - Платеж неудачен
- `payment_refunded` - Платеж возвращен

## Примеры использования

### Регистрация пользователя
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "client1",
    "email": "client@example.com",
    "password": "password123",
    "role": "client",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Авторизация
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "client1",
    "password": "password123"
  }'
```

### Создание заказа
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": 1,
    "description": "Нужна уборка квартиры",
    "address": "ул. Примерная, 123",
    "scheduled_date": "2025-08-28T10:00:00Z",
    "quantity": 1
  }'
```

### Оплата заказа
```bash
curl -X POST http://localhost:8000/api/payments/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": "card",
    "card_number": "4111111111111111",
    "card_expiry": "12/25",
    "card_cvv": "123",
    "card_holder_name": "John Doe"
  }'
```

## Статусы

### Order Status
- `pending` - Ожидает оплаты
- `paid` - Оплачен
- `in_progress` - В процессе выполнения
- `completed` - Завершен
- `canceled` - Отменен

### Payment Status
- `pending` - Ожидает обработки
- `processing` - Обрабатывается
- `completed` - Завершен
- `failed` - Неудачен
- `canceled` - Отменен
- `refunded` - Возвращен

## Коды ошибок

| Код | Описание |
|-----|----------|
| 400 | Bad Request - Неверные данные |
| 401 | Unauthorized - Требуется авторизация |
| 403 | Forbidden - Недостаточно прав |
| 404 | Not Found - Ресурс не найден |
| 500 | Internal Server Error - Внутренняя ошибка сервера |

## Swagger UI

Интерактивная документация доступна по адресам:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`
