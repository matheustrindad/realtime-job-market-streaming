import json
import time
import requests
from kafka import KafkaProducer

# Configurações da API (Use suas chaves do Projeto 1)
APP_ID = "SUA_APP_ID"
APP_KEY = "SUA_APP_KEY"

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_and_send_jobs():
    url = f"https://api.adzuna.com/v1/api/jobs/br/search/1?app_id={APP_ID}&app_key={APP_KEY}&results_per_page=10&what=data%20engineer"
    
    response = requests.get(url)
    if response.status_code == 200:
        jobs = response.json().get('results', [])
        for job in jobs:
            # Simplificando o JSON para o Kafka
            job_data = {
                "id": job.get('id'),
                "title": job.get('title'),
                "company": job.get('company', {}).get('display_name'),
                "location": job.get('location', {}).get('display_name'),
                "salary_min": job.get('salary_min'),
                "timestamp": time.time()
            }
            producer.send('job-events', value=job_data)
            print(f"Vaga Real Enviada: {job_data['title']} em {job_data['company']}")
        producer.flush()

if __name__ == "__main__":
    while True:
        fetch_and_send_jobs()
        print("Aguardando 10 minutos para a próxima coleta...")
        time.sleep(600) # Evita estourar o limite da API