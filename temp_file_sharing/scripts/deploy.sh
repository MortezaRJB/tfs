echo "Starting deployment..."

# Pull latest code
git pull origin main

# Build and start containers
docker-compose down
docker-compose build
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Health check
echo "Performing health check..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/)

if [ $response = "200" ]; then
    echo "Deployment successful! Health check passed."
else
    echo "Deployment failed! Health check returned: $response"
    exit 1
fi