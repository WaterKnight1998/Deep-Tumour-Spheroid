# Build and launch WebApp

docker build -t tfg-flask:latest .

docker run -d -p 5000:5000 tfg-flask