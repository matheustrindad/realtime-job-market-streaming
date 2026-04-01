import os
import json
import time
import requests
from kafka import KafkaProducer
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

producer = KafkaProducer(
    bootstrap_servers=['localhost:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Lista dos países que focamos no Projeto 1
COUNTRIES = ['br', 'us', 'gb', 'ca']

def fetch_and_send_jobs():
    for country in COUNTRIES:
        print(f"📡 Coletando vagas em: {country.upper()}...")
        
        # O parâmetro {country} agora é dinâmico na URL
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1?app_id={APP_ID}&app_key={APP_KEY}&results_per_page=10&what=data%20engineer"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                jobs = response.json().get('results', [])
                for job in jobs:
                    job_data = {
                        "id": job.get('id'),
                        "title": job.get('title'),
                        "company": job.get('company', {}).get('display_name'),
                        # Adicionamos o país à localização para facilitar a visualização
                        "location": f"{job.get('location', {}).get('display_name')} ({country.upper()})",
                        "salary_min": job.get('salary_min'),
                        "timestamp": time.time(),
                        "job_url": job.get('redirect_url') # Campo essencial para o novo Dashboard
                    }
                    producer.send('job-events', value=job_data)
                    print(f"✅ [{country.upper()}] Vaga Enviada: {job_data['title']}")
                
                producer.flush()
            else:
                print(f"❌ Erro na API Adzuna ({country}): {response.status_code}")
        
        except Exception as e:
            print(f"⚠️ Falha ao conectar na API ({country}): {e}")
        
        # Pequena pausa entre países para não dar Rate Limit
        time.sleep(2)

if __name__ == "__main__":
    while True:
        fetch_and_send_jobs()
        print("\n🌍 Ciclo completo! Aguardando 10 minutos para a próxima coleta global...")
        # Tempo de espera de 10 minutos (600 segundos) para respeitar a API
        time.sleep(600)