# xpensi - Smart Control of Small Expenses

A modern web application to control those small daily expenses that go unnoticed but add up to significant amounts by the end of the year.

![Django](https://img.shields.io/badge/Django-5.2.3-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/Django%20REST-Framework-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![HTMX](https://img.shields.io/badge/HTMX-1.9-336791?style=for-the-badge&logo=htmx&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-3.4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)

## Concept: Small Expenses ("Ant Expenses")

**Small expenses** are minor daily outlays that individually seem insignificant, but when accumulated, represent a considerable part of your budget:

- Daily coffee: ₹2.50 × 365 days = ₹912 per year
- Impulsive delivery: ₹12 × 2 times/week = ₹1,248 per year  
- Unnecessary taxis: ₹7 × 3 times/week = ₹1,092 per year
- Unused subscriptions: ₹9 × 12 months = ₹108 per year

**Total: ₹3,360 per year in "small" expenses**

## Screenshots

### Main Dashboard
The main view with real-time metrics, interactive charts, and a list of recent expenses.

![Main Dashboard](screenshots/desktop/dashboard-complete-desktop.png)

### Expense Management
Complete list of expenses with advanced filters and full CRUD functionality.

![Expense List](screenshots/desktop/expense-list-desktop.png)

### Interactive Modals (HTMX)
Dynamic forms that open without reloading the page.

| Add Expense | Edit Expense |
|-------------|-------------|
| ![Add Expense](screenshots/desktop/add-expense-modal-desktop.png) | ![Edit Expense](screenshots/desktop/edit-expense-modal-desktop.png) |

### User Profile
Personal settings and automatic alerts for monthly reports.

![User Profile](screenshots/desktop/user-profile-desktop.png)

### Key Features

#### Access and Authentication
Login page with a clean and professional design.

![Login](screenshots/desktop/login-desktop.png)

#### Budget Management
Modal to set monthly budget and automatic alerts.

![Budget](screenshots/desktop/budget-modal-desktop.png)

#### Responsive Design
The app adapts perfectly to mobile devices with optimized navigation and touch-friendly forms.

#### Advanced Filters
Smart filtering system by period, category, and amount.

![Active Filters](screenshots/desktop/expense-filters-active-desktop.png)

### Mobile Version

The app features a fully responsive design that adapts perfectly to mobile devices.

#### Main Mobile Interface
Dashboard optimized for small screens with intuitive navigation.

<img src="screenshots/mobile/dashboard-mobile.png" alt="Dashboard Mobile" width="300">

#### Mobile Navigation
Hamburger menu with quick access to all features.

<img src="screenshots/mobile/mobile-menu.png" alt="Mobile Menu" width="300">

#### Mobile Access
Login page optimized for touch devices.

<img src="screenshots/mobile/login-mobile.png" alt="Login Mobile" width="300">

#### Mobile Expense Management
Expense list and forms adapted for mobile.

<table>
<tr>
<td><strong>Expense List</strong></td>
<td><strong>Add Expense</strong></td>
</tr>
<tr>
<td><img src="screenshots/mobile/expense-list-mobile.png" alt="Expense List Mobile" width="300"></td>
<td><img src="screenshots/mobile/add-expense-mobile.png" alt="Add Expense Mobile" width="300"></td>
</tr>
</table>

#### Mobile Settings
User profile and settings optimized for mobile.

<img src="screenshots/mobile/user-profile-mobile.png" alt="User Profile Mobile" width="300">

## Main Features

### Smart Dashboard
- Real-time metrics with period filters
- Interactive charts (doughnut and line) with Chart.js
- Auto-update without page reload (HTMX)
- Responsive design optimized for mobile

### Visual Analysis
- Category distribution with custom colors
- Time trends to identify patterns
- Automatic annual projections
- Monthly comparisons

### User Experience
- HTMX interface without page reloads
- Dynamic modals for CRUD operations
- Auto-refresh in lists and metrics
- Smooth navigation between sections

### Advanced Features
- Smart filters by date, category, and amount
- Full CRUD with real-time validation
- Category system with custom colors
- User management with secure authentication
- Automated budget alert system
- **REST API**: Specific endpoints for integration
- **Automated Reports**: Monthly report generation

## Technologies

### Backend
- **Django 5.2.3**: Robust web framework
- **Django REST Framework**: REST API
- **PostgreSQL**: Database for development and production
- **Python 3.12**: Base language
- **Gunicorn**: WSGI server for production

### Frontend
- **HTMX**: Interactivity without complex JavaScript
- **Tailwind CSS**: CSS utility framework
- **Chart.js**: Interactive charts
- **Alpine.js**: Lightweight interactivity

## Installation

### Prerequisites
- Python 3.12 and pip
- PostgreSQL
- Git

### Quick Setup
```bash
# Clone repository
git clone https://github.com/your-username/xpensi.git
cd xpensi

# Set environment variables
cp .env.example .env.local

# Install dependencies
pip install -r requirements.txt

# Set up the database (create user and database in PostgreSQL if needed)

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Run Commands

```bash
# 1. Clone the repository
git clone https://github.com/your-username/xpensi.git
cd xpensi

# 2. Copy environment variables file
cp .env.example .env.local

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set up PostgreSQL database if not already created

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

### How to Run This Project Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/xpensi.git
   cd xpensi
   ```

2. **Copy environment variables file**
   ```bash
   cp .env.example .env.local
   ```
   Edit `.env.local` if needed (database, email, etc).

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**  
   Create a database and user as specified in `.env.local`. Example:
   ```sql
   CREATE DATABASE gastos_hormiga_dev;
   CREATE USER postgres WITH PASSWORD 'postgres';
   GRANT ALL PRIVILEGES ON DATABASE gastos_hormiga_dev TO postgres;
   ```

5. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the app**
   - Main app: http://localhost:8000/
   - Admin: http://localhost:8000/admin/

## Project Structure

```
xpensi/
├── apps/
│   ├── core/                     # Base utilities and templates
│   ├── expenses/                 # Main expenses app
│   │   ├── api/                 # REST API
│   │   │   ├── authentication.py # Bearer token auth
│   │   │   ├── serializers.py   # DRF serializers
│   │   │   ├── views.py         # API views
│   │   │   └── urls.py          # API endpoints
│   │   ├── models.py            # Category, Expense, Budget
│   │   ├── views.py             # Web business logic
│   │   ├── forms.py             # Forms with validation
│   │   ├── utils/               # Modularized utilities
│   │   ├── templates/           # Specialized templates
│   │   └── static/              # Specific CSS and JS
│   └── users/                   # User management
├── config/                      # Django configuration
│   ├── settings/                # Modular settings
│   │   ├── base.py             # Base config + REST API
│   │   ├── local.py            # Development
│   │   └── production.py       # Production
│   └── urls.py                 # Main URLs + API
├── static/                      # Global static files
├── requirements.txt             # Python + DRF dependencies
```

## Application Usage

### Main Dashboard
- Metrics for the selected period
- Category distribution chart  
- Expense time trend
- List of recent expenses

### Expense Management
- Add new expense (HTMX modal)
- Edit existing expense (HTMX modal)
- Delete expense (confirmation)
- View full details

### Advanced Filters
- By period (This month, last month, last 7/30 days)
- By category (Coffee, Delivery, Transport, etc.)
- By custom date range
- By amount range (min/max)

### Alerts and Reports System
- Automatic alerts when reaching 90% of monthly budget
- Per-user configuration (enable/disable)
- **Automated Monthly Reports**
- **REST API**: Specific integration
- **Smart Analysis**: Custom AI by user and period

## Useful Commands

### Development
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Run tests
python manage.py test

# Access Django shell
python manage.py shell
```

### API Testing
```bash
# Test active users endpoint
curl -H "Authorization: Bearer {token}" http://localhost:8000/api/users/active/

# Test full user endpoint  
curl -H "Authorization: Bearer {token}" http://localhost:8000/api/users/1/complete/

# Check API documentation
curl http://localhost:8000/api/docs/
```

## REST API (Django REST Framework)

The app includes **2 specific endpoints** developed with Django REST Framework for automated reports.

### Available Endpoints

#### List Active Users
```
GET /api/users/active/
Authorization: Bearer {TOKEN}
```

**Purpose**: Get a list of users eligible for automated reports

**Returns users who**:
- Have a budget configured
- Have email alerts enabled  
- Have recorded expenses in the last 30 days

#### Get Complete User Data

#### Interactive Documentation
- **Swagger UI**: http://localhost:8000/api/docs/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### API Authentication
- **Development**: Fixed token in settings
- **Production**: Secure token via environment variables
- **Type**: Custom Bearer Token

---

**Note:** This project is configured for local development only, without Docker or external automation.