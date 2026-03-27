@echo off
echo 🚀 Iniciando infraestrutura do Job Market...
docker-compose up -d
echo ⏳ Aguardando o Kafka estabilizar (30s)...
timeout /t 30

echo 📬 Criando topicos no Kafka...
docker exec -it kafka kafka-topics --create --bootstrap-server kafka:9092 --topic job-events --partitions 1 --replication-factor 1 --if-not-exists
docker exec -it kafka kafka-topics --create --bootstrap-server kafka:9092 --topic job-events-dlq --partitions 1 --replication-factor 1 --if-not-exists

echo 🗄️ Resetando e preparando a tabela no PostgreSQL...
docker exec -it postgres-db psql -U user -d job_market -c "DROP TABLE IF EXISTS job_events CASCADE;"
docker exec -it postgres-db psql -U user -d job_market -c "CREATE TABLE job_events (title TEXT, company TEXT, location TEXT, salary_min FLOAT, timestamp TEXT, job_url TEXT, is_anomaly BOOLEAN, event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"

echo ✅ Setup completo! Rode agora o run_spark.bat.
pause