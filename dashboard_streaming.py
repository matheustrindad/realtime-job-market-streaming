import streamlit as st
import pandas as pd
import psycopg2
import time

st.set_page_config(page_title="Real-Time Job Market", layout="wide")
st.title("Real-Time Job Market Streaming Pipeline")
st.caption("Live data from Kafka + Spark + PostgreSQL")

def get_data():
    conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="job_market", user="user", password="password"
    )
    df = pd.read_sql("SELECT * FROM v_job_market_analysis LIMIT 500", conn)
    conn.close()
    return df

def get_stats():
    conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="job_market", user="user", password="password"
    )
    stats = pd.read_sql("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomalies,
            ROUND(AVG(salary_min)::numeric, 2) as avg_salary,
            COUNT(DISTINCT company) as companies
        FROM job_events
    """, conn)
    conn.close()
    return stats

# Auto-refresh
refresh = st.sidebar.slider("Auto-refresh (segundos)", 5, 60, 10)
st.sidebar.info(f"Atualizando a cada {refresh}s")

stats = get_stats()
df = get_data()

# Métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Eventos", int(stats['total'][0]))
col2.metric("Anomalias Detectadas", int(stats['anomalies'][0]))
col3.metric("Salário Médio", f"${float(stats['avg_salary'][0]):,.2f}")
col4.metric("Empresas", int(stats['companies'][0]))

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribuição de Status")
    st.bar_chart(df['status_vaga'].value_counts())

with col2:
    st.subheader("Top Empresas")
    st.bar_chart(df['company'].value_counts().head(10))

st.subheader("Eventos Recentes")
st.dataframe(
    df[['title','company','location','salary_min','status_vaga','event_date']],
    use_container_width=True
)

time.sleep(refresh)
st.rerun()