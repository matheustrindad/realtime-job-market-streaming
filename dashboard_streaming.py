import streamlit as st
import pandas as pd
import psycopg2
import time
import plotly.express as px

st.set_page_config(page_title="Real-Time Job Market", layout="wide")
st.title("Real-Time Job Market Streaming Pipeline")
st.caption("Live data from Kafka + Spark + PostgreSQL")

def get_data():
    conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="job_market", user="user", password="password"
    )
    query = """
        SELECT 
            title, company, location, salary_min, job_url, is_anomaly, timestamp,
            CASE 
                WHEN is_anomaly THEN '🔥 Anomalia'
                WHEN salary_min > 0 THEN '✅ Normal'
                ELSE '⚠️ Sem Info'
            END as status_vaga
        FROM job_events
        ORDER BY timestamp DESC
        LIMIT 500
    """
    df = pd.read_sql(query, conn)
    conn.close()
    if not df.empty:
        df['event_date'] = pd.to_datetime(df['timestamp'].astype(float), unit='s')
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
            ROUND(AVG(NULLIF(salary_min, 0))::numeric, 2) as avg_salary,
            COUNT(DISTINCT company) as companies,
            SUM(CASE WHEN salary_min > 0 THEN 1 ELSE 0 END) as with_salary,
            SUM(CASE WHEN salary_min = 0 THEN 1 ELSE 0 END) as no_salary
        FROM job_events
    """, conn)
    conn.close()
    return stats

# Interface
refresh = st.sidebar.slider("Auto-refresh (segundos)", 5, 60, 10)
stats = get_stats()
df = get_data()

# Métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Eventos", int(stats['total'][0]))
col2.metric("Anomalias", int(stats['anomalies'][0]))
col3.metric("Salário Médio", f"${float(stats['avg_salary'][0] or 0):,.2f}")
col4.metric("Empresas", int(stats['companies'][0]))

st.divider()

# Gráficos
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Distribuição de Status")
    st.bar_chart(df['status_vaga'].value_counts())
with col2:
    st.subheader("Transparência Salarial")
    labels = ['Com Salário', 'Sem Salário']
    values = [int(stats['with_salary'][0]), int(stats['no_salary'][0])]
    fig = px.pie(names=labels, values=values, color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
with col3:
    st.subheader("Top Empresas")
    st.bar_chart(df['company'].value_counts().head(10))

# Tabela
st.subheader("Eventos Recentes")
st.dataframe(
    df[['title', 'company', 'location', 'salary_min', 'status_vaga', 'event_date', 'job_url']],
    column_config={
        "job_url": st.column_config.LinkColumn("Link da Vaga"),
        "salary_min": st.column_config.NumberColumn("Salário ($)", format="$%.2f"),
        "event_date": "Data/Hora"
    },
    use_container_width=True,
    hide_index=True,
)

time.sleep(refresh)
st.rerun()