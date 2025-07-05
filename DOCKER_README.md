# Docker Deployment Guide

This guide explains how to deploy the FastAPI Medical Records System using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

## Quick Start

### 1. Build and Run with Docker Compose (Recommended)

```bash
# Build and start the application
docker-compose up --build

# Run in detached mode
docker-compose up -d --build
```

### 2. Initialize Database (First Time Only)

```bash
# Run the database initialization service
docker-compose --profile init up db-init
```

### 3. Access the Application

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

## Manual Docker Commands

### Build the Image

```bash
docker build -t medical-records-api .
```

### Run the Container

```bash
docker run -p 8000:8000 \
  -e ULTRASAFE_API_KEY=your-api-key \
  -e ULTRASAFE_API_BASE=https://api.ultrasafe.ai \
  -e VALID_API_KEY=secret-dev-key \
  -v $(pwd)/medical_records.db:/app/medical_records.db \
  -v $(pwd)/chroma_db:/app/chroma_db \
  medical-records-api
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
ULTRASAFE_API_KEY=your-ultrasafe-api-key
ULTRASAFE_API_BASE=https://api.ultrasafe.ai
VALID_API_KEY=your-secret-api-key
```

## Data Persistence

The Docker setup includes volume mounts for:
- `medical_records.db`: SQLite database file
- `chroma_db/`: ChromaDB vector database directory

This ensures your data persists between container restarts.

## Health Checks

The container includes a health check that verifies the API is responding:
- Checks every 30 seconds
- Timeout of 10 seconds
- Retries 3 times before marking as unhealthy

## Stopping the Application

```bash
# Stop and remove containers
docker-compose down

# Stop and remove containers, networks, and volumes
docker-compose down -v
```

## Troubleshooting

### View Logs

```bash
# View logs for all services
docker-compose logs

# View logs for specific service
docker-compose logs medical-records-api

# Follow logs in real-time
docker-compose logs -f
```

### Access Container Shell

```bash
# Access running container
docker-compose exec medical-records-api bash

# Or with manual Docker
docker exec -it <container-id> bash
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up --build

# Or rebuild specific service
docker-compose build medical-records-api
```

## Production Considerations

For production deployment, consider:

1. **Environment Variables**: Use proper secrets management
2. **Database**: Consider using PostgreSQL instead of SQLite
3. **Vector Database**: Use a managed service like Pinecone or Weaviate
4. **Reverse Proxy**: Add nginx or similar for SSL termination
5. **Monitoring**: Add logging and monitoring solutions
6. **Security**: Review and harden the container security

## API Usage with Docker

Once running, you can test the API:

```bash
# Health check
curl http://localhost:8000/

# Create a medical record
curl -X POST "http://localhost:8000/api/v1/records/" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: secret-dev-key" \
  -d '{
    "patient_id": 1,
    "record_content": "Patient shows signs of recovery from bronchitis."
  }'

# Search records
curl -X GET "http://localhost:8000/api/v1/search/?q=hypertension%20management" \
  -H "X-API-KEY: secret-dev-key"
```

## Dockerfile Changes

The Dockerfile has been updated to ensure the directories are writable:

```dockerfile
# After creating the directories, ensure they're writable
RUN mkdir -p chroma_db && chmod 777 chroma_db
``` 