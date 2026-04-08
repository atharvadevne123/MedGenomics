# MedGenomics Healthcare Data Lake Dashboard

A comprehensive healthcare data management system with a modern web dashboard for managing patient records and medical supplies inventory.

## 🎯 Overview

MedGenomics is a full-stack healthcare data lake application built with FastAPI, PostgreSQL, and a responsive web interface. It manages 10,000+ patient records and 8,000+ medical supply items with real-time analytics and filtering capabilities.

## ✨ Features

### 🔐 Authentication System (NEW!)
- **User Registration**: Create new user accounts with email validation
- **User Login**: Secure login with JWT token authentication
- **JWT Tokens**: 24-hour token expiration with role-based access control
- **Role-Based Access**: Support for admin, doctor, lab_tech, and viewer roles
- **Secure Password Hashing**: SHA256 password encryption
- **Protected Endpoints**: CRUD operations require valid JWT tokens

### Patient Management
- **10,000+ patient records** with comprehensive genomic data
- **Create Patient**: Add new patient records with modal form
- **Read Patient**: View all patients or get individual patient details
- **Update Patient**: Edit patient information (name, age, risk score, DNA marker, conditions, genomic data)
- **Delete Patient**: Remove patient records from database
- **Patient Search**: Real-time search by patient name, ID, or DNA marker
- **Risk Level Filtering**: Filter patients by risk level (High >80%, Moderate 40-80%, Low <40%)
- **Detailed patient modals** with treatment information and genomic data
- Patient database model with `created_at` and `updated_at` timestamps

### Supply/Inventory Management
- **8,000+ medical supply items** with real-time inventory tracking
- **Create Supply**: Add new supply items with category, quantity, cost, supplier
- **Read Supply**: View all inventory items or get individual item details
- **Update Supply**: Edit supply information (name, category, quantity, reorder point, location, supplier)
- **Delete Supply**: Remove inventory items from database
- **Inventory Search**: Real-time search by item name, supplier, or location
- **Stock Status Filtering**: Filter by stock level (Critical <50%, Low 50-150%, Healthy >150%)
- **Real-time stock status** (Critical/Low/Healthy) with color-coded indicators
- **Cost tracking** and total inventory value calculations
- **Reorder Point Alerts**: Automatic alerts when stock falls below threshold
- Inventory database model with `created_at` and `updated_at` timestamps

### Search & Filter Functionality
- **Patient Pool Search**: Search by name, ID, or DNA marker with instant results
- **Patient Risk Filtering**: Filter by risk level categories
- **Inventory Search**: Search supplies by name, supplier, or category
- **Inventory Status Filtering**: Filter by stock status (Critical/Low/Healthy)
- **Real-time Updates**: Filters update instantly as you type
- **Filter Reset**: Clear all filters with one click

### Analytics Dashboard
- **Real-time KPI statistics**
  - Total patient count
  - Average patient age
  - High-risk patient count
  - Active treatment count
- **Top conditions chart** showing disease prevalence
- **Risk distribution** visualization (Low/Medium/High)

### Data Operations
- Export patient data to CSV
- Real-time search functionality
- Side-by-side folder view (Patients & Supplies)
- Responsive modal details for each record
- Data refresh capability

## 🏗️ Architecture
```
MedGenomics/
├── src/
│   └── main.py              # FastAPI backend
├── static/
│   └── dashboard.html       # Single-file React-like frontend
├── docker-compose.yml       # Docker orchestration
├── Dockerfile              # API container definition
├── requirements.txt        # Python dependencies
└── scripts/               # Utility scripts (seeding, etc)
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (or Python 3.11+ with pip)
- Git
- Mac/Linux (or WSL on Windows)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/atharvadevne123/MedGenomics.git
cd MedGenomics
```

2. **Start the application (Docker)**
```bash
docker compose up -d
sleep 20
```

3. **Or Start locally (Python)**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

4. **Access the application**
```bash
# Login page
open http://localhost:8000/login

# Or registration
open http://localhost:8000/register
```

### Default Test Credentials
After starting the application, you can register a new account via:
- **Login Page**: `http://localhost:8000/login` - Sign in with existing credentials
- **Register Page**: `http://localhost:8000/register` - Create a new account

### Verify Installation
```bash
# Check API health
curl http://localhost:8000/health

# Test user registration
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"test123"}'

# Test user login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'
```

## 📊 Database Schema

### Patients Table
```sql
- id (VARCHAR PRIMARY KEY): pat_0000001 to pat_0010000
- name (VARCHAR): Unique patient names
- conditions (JSONB): Array of medical conditions
- genomic_data (JSONB): 
  - age, gender, address
  - risk_score (0-99)
  - mutations, medical_history
  - last_visit, location
  - current_treatment, treatment_status
  - admission_date
```

### Inventory Table
```sql
- id (VARCHAR PRIMARY KEY): s_000001 to s_008000
- item_name (VARCHAR): Supply name
- category (VARCHAR): Medications, Diagnostics, Equipment, Supplies
- qty_on_hand (INTEGER): Current stock
- reorder_point (INTEGER): Stock alert threshold
- cost (NUMERIC): Unit cost
- location (VARCHAR): Storage location
- supplier (VARCHAR): Supplier name
```

## 🔧 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register new user account |
| POST | `/api/login` | Login and get JWT token |

### Patient Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/patients` | Retrieve all patients (10,000+ records) |
| POST | `/api/patients` | Create new patient (requires auth) |
| GET | `/api/patients/{patient_id}` | Get specific patient details |
| PUT | `/api/patients/{patient_id}` | Update patient information (requires auth) |
| DELETE | `/api/patients/{patient_id}` | Delete patient record (requires auth) |
| GET | `/api/patients/search` | Search patients by query, risk level |

### Supply/Inventory Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/inventory` | Retrieve all inventory items (8,000+ records) |
| POST | `/api/inventory` | Create new supply item (requires auth) |
| GET | `/api/inventory/{item_id}` | Get specific inventory item details |
| PUT | `/api/inventory/{item_id}` | Update inventory item (requires auth) |
| DELETE | `/api/inventory/{item_id}` | Delete inventory item (requires auth) |
| GET | `/api/inventory/search` | Search inventory by query, category, status |

### Health & Status
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API health check |

## 📱 Dashboard Features

### Login & Registration Pages (NEW!)
- **Login Page** (`/login`): Secure user authentication with JWT tokens
- **Registration Page** (`/register`): Create new user accounts
- **Session Management**: Automatic token storage and validation
- **Error Handling**: Clear error messages for failed login/registration

### Dashboard View (Clinical Overview)
- **KPI Cards**: Key metrics dashboard
- **System Health**: Real-time status monitoring
- **Alerts Panel**: Important notifications and alerts
- **Activity Timeline**: Recent system activities

### Patient Pool View
- **Patient Search Bar**: Real-time search by name, ID, or DNA marker
- **Risk Level Filter**: Filter by High (>80%), Moderate (40-80%), or Low (<40%)
- **Patient Cards**: Display patient information with risk indicators
- **Patient Details Panel**: Click to view comprehensive patient information
- **Add New Patient Button**: Modal form to create new patient records
- **Edit Patient**: In-place editing with modal form
- **Delete Patient**: Remove patient records with confirmation

### Inventory Pool View
- **Inventory Search**: Real-time search by item name, supplier, or location
- **Category Filter**: Filter by Kits, Reagents, or Equipment
- **Stock Status Filter**: Filter by Critical, Low, or Healthy stock levels
- **Low Stock Alert**: Real-time count of items below reorder point
- **Supply Cards**: Display inventory with stock level visualization
- **Supply Details Panel**: Click to view complete inventory information including pricing
- **Add New Supply Button**: Modal form to create new inventory items
- **Edit Supply**: In-place editing with modal form
- **Delete Supply**: Remove inventory items with confirmation
- **Cost Tracking**: Total value calculations per item

### Analytics View
- **4 KPI Cards**: Key metrics overview
- **Conditions Chart**: Top 8 conditions by prevalence
- **Risk Distribution**: Pie-style bar chart (Low/Med/High)
- **Real-time Calculations**: Updates based on current data

### Genomic Records View
- **Records Table**: Complete genomic data for all patients
- **Patient ID**: Unique patient identifier
- **Gene Information**: Gene and variant data
- **Risk Level**: Color-coded risk indicators
- **Status**: Current patient status (Active/Critical)

### Export
- Export all patient data to CSV
- Includes: Name, Age, Risk Score, Treatment Status

## 🗄️ Data Management

### Seed Data (10,000 Patients)
Patients have unique first and last names with varied:
- Ages (18-95 years)
- Risk scores (10-99 scale)
- Medical conditions
- Treatment statuses
- Addresses and locations

### Seed Data (8,000 Supplies)
Supplies include:
- 4 categories: Medications, Diagnostics, Equipment, Supplies
- Stock quantities (5-500 units)
- Cost tracking ($10-$10,000)
- Multiple locations and suppliers

## 🛠️ Tech Stack

**Backend**
- FastAPI 0.104+
- SQLAlchemy ORM
- PostgreSQL 16 Alpine
- Python 3.11

**Frontend**
- Vanilla JavaScript (ES6+)
- HTML5
- CSS3 (Grid, Flexbox)
- Single-file architecture (no build tools)

**DevOps**
- Docker & Docker Compose
- PostgreSQL persistence volume
- Network isolation

## 📈 Performance

- **API Response Time**: ~50-100ms for full dataset
- **Patient Load**: 10,000 records
- **Supply Load**: 8,000 records
- **Search**: Real-time filtering <100ms
- **Database**: PostgreSQL with JSONB indexing

## 🔐 Security Features

### Authentication & Authorization
- **JWT Tokens**: JSON Web Tokens with 24-hour expiration
- **Password Hashing**: SHA256 encryption for password security
- **HTTPBearer Scheme**: Secure token validation on protected endpoints
- **Role-Based Access Control**: Multiple user roles (admin, doctor, lab_tech, viewer)
- **Token Validation**: Automatic token verification on CRUD operations

### Protected Endpoints
The following endpoints require valid JWT authentication:
- `POST /api/patients` - Create patient
- `PUT /api/patients/{patient_id}` - Update patient
- `DELETE /api/patients/{patient_id}` - Delete patient
- `POST /api/inventory` - Create inventory item
- `PUT /api/inventory/{item_id}` - Update inventory item
- `DELETE /api/inventory/{item_id}` - Delete inventory item

### Additional Security Recommendations for Production
- Use environment variables for database credentials
- Implement HTTPS/TLS encryption
- Add rate limiting to prevent abuse
- Implement additional input validation
- Use stronger password hashing (bcrypt/argon2 with salt)
- Add CORS restrictions to trusted origins only
- Implement audit logging for all data modifications
- Use prepared statements (already done via SQLAlchemy ORM)

## 📝 Environment Variables

Create a `.env` file:
```
DATABASE_URL=postgresql://admin:secure123@localhost:5432/medgenomics
API_PORT=8000
DEBUG=False
```

## 🐛 Troubleshooting

### Port 8000 already in use
```bash
# Find and kill process on port 8000
lsof -i :8000
kill -9 <PID>
```

### Database connection error
```bash
# Check PostgreSQL is running
docker compose ps

# Restart containers
docker compose down -v
docker compose up -d
sleep 20
```

### Data not loading
```bash
# Verify data exists
docker compose exec -T postgres psql -U admin -d medgenomics -c "SELECT COUNT(*) FROM patients;"

# Should return 10000
```

### Cache issues
- Clear browser cache: `Cmd + Shift + R` (Safari/Chrome)
- Open incognito/private window
- Check DevTools Console for errors (F12)

## 📚 Project Structure
```
MedGenomics/
├── src/
│   └── main.py                    # FastAPI app with authentication, CRUD operations
├── static/
│   ├── index.html                 # Dashboard - Clinical Overview
│   ├── patient-pool.html          # Patient management with CRUD modals
│   ├── inventory.html             # Inventory management with CRUD modals
│   ├── analytics.html             # Analytics and KPI dashboard
│   ├── genomic-records.html       # Genomic data records table
│   ├── login.html                 # User login page (NEW!)
│   └── register.html              # User registration page (NEW!)
├── venv/                          # Python virtual environment
├── docker-compose.yml             # Service orchestration
├── Dockerfile                     # Image definition
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python packages
├── README.md                      # This file
└── scripts/
    └── bulk_seed.py               # Data seeding utilities
```

## 🚢 Deployment

### Local Docker
```bash
docker compose up -d
```

### Production (AWS/GCP/Azure)
1. Build image: `docker build -t medgenomics-api .`
2. Push to registry: `docker tag medgenomics-api user/medgenomics-api:latest`
3. Deploy with Kubernetes or managed services

## 📖 API Documentation

**Swagger UI** available at: `http://localhost:8000/docs`
**ReDoc** available at: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**Atharva Devne**
- GitHub: [@atharvadevne123](https://github.com/atharvadevne123)
- Project: [MedGenomics](https://github.com/atharvadevne123/MedGenomics)

## 🙏 Acknowledgments

- Built with FastAPI and PostgreSQL
- Inspired by healthcare data management best practices
- Docker containerization for easy deployment

## 📞 Support

For issues, questions, or suggestions:
1. Check existing GitHub Issues
2. Create new Issue with detailed description
3. Include error messages and steps to reproduce

---

**Last Updated**: April 2026
**Status**: ✅ Active Development
**Version**: 2.0.0

## 🎉 Latest Release (v2.0.0) - April 2026

### New Features
- ✅ **Full Authentication System** with JWT tokens and role-based access control
- ✅ **Patient CRUD Operations** - Create, Read, Update, Delete patient records
- ✅ **Inventory CRUD Operations** - Complete supply management with modals
- ✅ **Advanced Search & Filters** - Real-time filtering for both patients and inventory
- ✅ **Login & Registration Pages** - Secure user account management
- ✅ **Token-Protected API Endpoints** - Secure all CRUD operations

### Fixed Issues
- Improved password security with SHA256 hashing
- Enhanced UI/UX with modal forms for data entry
- Real-time filter updates without page reload
- Better error handling and validation
