import json
import time
import random
from kafka import KafkaProducer

# Configura o produtor para enviar dados ao Kafka local
producer = KafkaProducer(
    bootstrap_servers=['localhost:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("🚀 Iniciando Stress Test do Dia 4...")

for i in range(50):
    # Gerando dados normais
    data = {
        "title": f"Data Engineer {i}",
        "company": "Stress Test Corp",
        "location": "Remote",
        "salary_min": random.uniform(3000, 7000),
        "timestamp": str(time.time())
    }
    
    # Injetando 1 ANOMALIA (Salário muito acima da média do lote)
    if i == 25:
        data["salary_min"] = 95000.0
        print("🔥 Injetando uma ANOMALIA...")

    # Injetando 1 DADO INVÁLIDO (Salário negativo para a DLQ)
    if i == 49:
        data["salary_min"] = -1.0
        print("🗑️ Injetando um dado para a DLQ...")

    producer.send('job-events', value=data)
    time.sleep(0.05) # Envio rápido para testar o processamento em lote

producer.flush()
print("✅ 50 vagas enviadas! Verifique os terminais do Spark e da DLQ.")