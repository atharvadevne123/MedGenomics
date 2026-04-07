# MedGenomics Healthcare Data Lake Dashboard

A comprehensive healthcare data management system with a modern web dashboard for managing patient records and medical supplies inventory.

## 🎯 Overview

MedGenomics is a full-stack healthcare data lake application built with FastAPI, PostgreSQL, and a responsive web interface. It manages 10,000+ patient records and 8,000+ medical supply items with real-time analytics and filtering capabilities.

## ✨ Features

### Patient Management
- **10,000 unique patient records** with comprehensive genomic data
- Patient search and filtering by name
- Filter by treatment status (Active, Monitoring, Completed)
- Filter by risk level (High Risk patients)
- Sort by name or risk score
- Detailed patient modal with treatment information

### Supply Management
- **8,000 medical supply items** with inventory tracking
- Real-time stock status (Critical/OK)
- Cost tracking and total value calculations
- Supplier and location information
- Automatic reorder point alerts

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
- Docker & Docker Compose
- Git
- Mac/Linux (or WSL on Windows)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/atharvadevne123/MedGenomics.git
cd MedGenomics
```

2. **Start the application**
```bash
docker compose up -d
sleep 20
```

3. **Access the dashboard**
```bash
open http://10.0.0.223:8000
```
Or navigate to `http://localhost:8000` in your browser

### Verify Installation
```bash
# Check containers are running
docker compose ps

# Verify API health
curl http://localhost:8000/health
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

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API health check |
| GET | `/patients` | Retrieve all patients (10,000 records) |
| GET | `/inventory` | Retrieve all supplies (8,000 records) |
| POST | `/patients` | Create/update patient record |
| POST | `/inventory` | Create/update supply record |

## 📱 Dashboard Features

### Dashboard View
- **Search Bar**: Real-time patient search by name
- **Filter Buttons**: All Patients, Active Treatment, High Risk
- **Sort Options**: By Name or Risk Score
- **Two-Column Folder Layout**: 
  - Left: Patient records (scrollable)
  - Right: Supply inventory (scrollable)
- **Card Details**: Click any card to view full details in modal

### Analytics View
- **4 KPI Cards**: Key metrics overview
- **Conditions Chart**: Top 8 conditions by prevalence
- **Risk Distribution**: Pie-style bar chart (Low/Med/High)
- **Real-time Calculations**: Updates based on current data

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

## 🔐 Security Notes

This is a development/demo application. For production:
- Enable authentication (JWT/OAuth)
- Use environment variables for DB credentials
- Implement HTTPS/TLS
- Add rate limiting
- Implement input validation
- Use prepared statements (already done via SQLAlchemy)

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
/src
  └── main.py           # FastAPI app, models, routes
/static
  └── dashboard.html    # Complete frontend (CSS + JS included)
/scripts
  └── bulk_seed.py      # Data seeding utilities
docker-compose.yml      # Service orchestration
Dockerfile             # Image definition
requirements.txt       # Python packages
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

**Last Updated**: March 2026
**Status**: ✅ Active Development
**Version**: 1.0.0
