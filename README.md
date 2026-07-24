# 🍽️ MunchBot - AI Food Pre-Booking System

MunchBot is an AI-powered food pre-booking system built with **FastAPI** and **PostgreSQL**. It allows students to pre-order meals through a WhatsApp chatbot while providing cafeteria staff with an admin dashboard to efficiently manage orders, pickup slots, and notifications.

---

# ✨ Features

## 👨‍🎓 Student

- Register through WhatsApp
- Browse available food stalls
- View menu with pagination
- Add multiple items to cart
- Select pickup slot
- Place food orders
- Cancel pending orders
- Receive WhatsApp notifications
- OTP-based food collection

---

## 👨‍🍳 Admin

- View pending orders
- Confirm orders
- Start food preparation
- Mark orders as ready
- Verify OTP during pickup
- Cancel orders with reason
- Generate pickup slots
- Auto-cancel expired pending orders

---

## 🤖 WhatsApp Chatbot

- Student onboarding
- Interactive ordering flow
- Session management
- Menu navigation
- Cart management
- Pickup slot selection
- Order cancellation
- Help command
- Automatic session reset

---

## 📲 WhatsApp Notifications

Students receive real-time updates for:

- ✅ Order Received
- ✅ Order Confirmed
- ✅ Order Ready (with Pickup OTP)
- ✅ Order Completed
- ✅ Order Cancelled
- ✅ Auto Cancelled

---

# 🛠 Tech Stack

### Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic

### Authentication

- JWT Authentication
- Passlib (bcrypt)

### Messaging

- WhatsApp Cloud API

### Frontend

- HTML
- CSS
- JavaScript

---

# 📂 Project Structure

```
food-booking-ai/

│
├── app/
│   ├── api/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   ├── database.py
│   ├── config.py
│   └── main.py
│
├── frontend/
│
├── alembic/
│
├── tests/
│
├── requirements.txt
└── README.md
```

---

# 🚀 Workflow

```
Student
    │
    ▼
WhatsApp Chatbot
    │
    ▼
Browse Menu
    │
    ▼
Build Cart
    │
    ▼
Select Pickup Slot
    │
    ▼
Place Order
    │
    ▼
Admin Dashboard
    │
    ├── Confirm
    ├── Preparing
    ├── Ready (OTP Generated)
    ├── Verify OTP
    └── Complete
```

---

# 🔐 Security

- JWT Authentication
- Password Hashing
- OTP Verification
- Role-Based Access Control
- Input Validation

---

# 📦 Installation

```bash
git clone <repository-url>

cd food-booking-ai

python -m venv venv

source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create `.env`

```env
DATABASE_URL=
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=
WHATSAPP_TOKEN=
PHONE_NUMBER_ID=
VERIFY_TOKEN=
```

Run migrations

```bash
alembic upgrade head
```

Start server

```bash
uvicorn app.main:app --reload
```

---

# 📖 API Documentation

```
http://localhost:8000/docs
```

---

# 🎯 Key Features Demonstrated

- Clean Architecture
- Repository Pattern
- Service Layer
- REST API Design
- JWT Authentication
- SQLAlchemy ORM
- Alembic Migrations
- WhatsApp Integration
- OTP Verification
- Session Management
- Admin Dashboard
- Real-Time Notifications

---

# 📸 Screenshots

Add screenshots of:

- Login
- Dashboard
- Order Management
- WhatsApp Chat
- Pickup Slot Generation

---

# 🔮 Future Improvements

- AI meal recommendations
- Online payment integration
- QR code pickup
- Order analytics dashboard
- Inventory management
- Multi-language chatbot
- Push notifications

---

# 👨‍💻 Author

**Harsh Kumar**

Built as an industry-grade backend project using FastAPI, PostgreSQL, and WhatsApp Cloud API.