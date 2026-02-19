# K12 Answer Sheet Evaluator - Complete Command Reference

## 🚀 Quick Start (All Services)

### 1. Start PostgreSQL
```bash
brew services start postgresql@14
```

### 2. Start Qdrant (Vector Database)
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 3. Start Ollama (Local LLM)
```bash
ollama serve
# In another terminal:
ollama pull llama3.1:8b
```

### 4. Start Backend
```bash
cd /Users/ujwalsingamsetti/project-k12/k12-answer-evaluator/backend
source venv/bin/activate
unset DEBUG
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start Frontend
```bash
cd /Users/ujwalsingamsetti/project-k12/frontend
npm run dev
```

---

## 📦 Installation Commands

### Backend Setup
```bash
# Navigate to backend
cd /Users/ujwalsingamsetti/project-k12/k12-answer-evaluator/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py
```

### Frontend Setup
```bash
# Navigate to frontend
cd /Users/ujwalsingamsetti/project-k12/frontend

# Install dependencies
npm install

# Install additional packages
npm install react-router-dom axios react-hot-toast
npm install -D tailwindcss postcss autoprefixer @tailwindcss/postcss
```

---

## 🗄️ Database Commands

### PostgreSQL
```bash
# Install
brew install postgresql@14

# Start service
brew services start postgresql@14

# Stop service
brew services stop postgresql@14

# Create database
createdb k12_evaluator

# Drop database (if needed)
dropdb k12_evaluator

# Connect to database
psql k12_evaluator

# List all databases
psql -l
```

### Database Operations
```bash
# Initialize tables
cd /Users/ujwalsingamsetti/project-k12/k12-answer-evaluator/backend
source venv/bin/activate
python init_db.py

# Reset database (drop and recreate)
dropdb k12_evaluator && createdb k12_evaluator && python init_db.py
```

---

## 🐳 Docker Commands

### Qdrant (Vector Database)
```bash
# Start Qdrant
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Start with persistent storage
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Stop Qdrant
docker stop $(docker ps -q --filter ancestor=qdrant/qdrant)

# Remove Qdrant container
docker rm $(docker ps -aq --filter ancestor=qdrant/qdrant)
```

### Check Docker Status
```bash
# List running containers
docker ps

# List all containers
docker ps -a

# View logs
docker logs <container_id>
```

---

## 🤖 Ollama Commands

### Installation & Setup
```bash
# Install Ollama (if not installed)
brew install ollama

# Start Ollama service
ollama serve

# Pull Llama 3.1:8b model
ollama pull llama3.1:8b

# List installed models
ollama list

# Test model
ollama run llama3.1:8b "Hello, how are you?"
```

---

## 🔧 Backend Commands

### Development
```bash
cd /Users/ujwalsingamsetti/project-k12/k12-answer-evaluator/backend
source venv/bin/activate

# Start server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start without reload
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run in background
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# Stop background server
pkill -f "uvicorn app.main:app"
```

### Testing
```bash
# Test API
python test_api.py

# Check health
curl http://localhost:8000/api/health

# View API docs
open http://localhost:8000/docs
```

### Python Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Deactivate
deactivate

# Install package
pip install <package_name>

# Update requirements
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt
```

---

## 💻 Frontend Commands

### Development
```bash
cd /Users/ujwalsingamsetti/project-k12/frontend

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Package Management
```bash
# Install dependencies
npm install

# Install specific package
npm install <package_name>

# Install dev dependency
npm install -D <package_name>

# Update packages
npm update

# Remove package
npm uninstall <package_name>
```

---

## 🧪 Testing Commands

### Backend Tests
```bash
cd /Users/ujwalsingamsetti/project-k12/k12-answer-evaluator/backend
source venv/bin/activate

# Run API tests
python test_api.py

# Test specific endpoint
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","full_name":"Test","role":"teacher"}'
```

### Check Services
```bash
# Check PostgreSQL
psql -l

# Check Qdrant
curl http://localhost:6333/collections

# Check Ollama
curl http://localhost:11434/api/tags

# Check Backend
curl http://localhost:8000/api/health

# Check Frontend
curl http://localhost:5173
```

---

## 🔄 Complete Restart Sequence

```bash
# 1. Stop all services
brew services stop postgresql@14
docker stop $(docker ps -q)
pkill -f "uvicorn"
pkill -f "ollama"

# 2. Start all services
brew services start postgresql@14
docker run -d -p 6333:6333 qdrant/qdrant
ollama serve &

# 3. Start backend
cd /Users/ujwalsingamsetti/project-k12/k12-answer-evaluator/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# 4. Start frontend
cd /Users/ujwalsingamsetti/project-k12/frontend
npm run dev
```

---

## 📊 Service URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Qdrant**: http://localhost:6333
- **Ollama**: http://localhost:11434

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8000
lsof -i :5173

# Kill process
kill -9 <PID>
```

### Database Issues
```bash
# Reset database
dropdb k12_evaluator
createdb k12_evaluator
cd backend && python init_db.py
```

### Python Issues
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Node Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

## 📝 Environment Variables

### Backend (.env)
```bash
DATABASE_URL=postgresql://localhost/k12_evaluator
SECRET_KEY=your-secret-key
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:8b
QDRANT_URL=http://localhost:6333
GOOGLE_VISION_CREDENTIALS=./google-vision-credentials.json
```

---

## ✅ Health Check Script

```bash
#!/bin/bash
echo "Checking services..."
echo "PostgreSQL: $(pg_isready && echo '✅' || echo '❌')"
echo "Qdrant: $(curl -s http://localhost:6333/collections > /dev/null && echo '✅' || echo '❌')"
echo "Ollama: $(curl -s http://localhost:11434/api/tags > /dev/null && echo '✅' || echo '❌')"
echo "Backend: $(curl -s http://localhost:8000/api/health > /dev/null && echo '✅' || echo '❌')"
echo "Frontend: $(curl -s http://localhost:5173 > /dev/null && echo '✅' || echo '❌')"
```

Save as `check_services.sh` and run: `bash check_services.sh`
