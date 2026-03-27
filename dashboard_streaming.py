import streamlit as st
import pandas as pd
import psycopg2
import time
import plotly.express as px
import plotly.graph_objects as go

# ========== CONFIGURAÇÃO ==========
st.set_page_config(
    page_title="Job Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS DARK MODE PREMIUM ==========
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Fundo principal - Dark */
    .stApp {
        background: #0a0118;
    }
    
    /* Container principal */
    .block-container {
        background: linear-gradient(135deg, #1a0b2e 0%, #16001e 100%);
        border-radius: 30px;
        padding: 2.5rem;
        border: 1px solid rgba(139, 92, 246, 0.1);
    }
    
    /* Sidebar escura */
    section[data-testid="stSidebar"] {
        background: #0f0320;
        border-right: 1px solid rgba(139, 92, 246, 0.15);
    }
    
    section[data-testid="stSidebar"] * {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Cards de métrica - Dark com borda neon */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e1139 0%, #1a0b2e 100%);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 20px;
        padding: 1.8rem;
        box-shadow: 0 8px 32px rgba(139, 92, 246, 0.1);
        transition: all 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border-color: rgba(139, 92, 246, 0.6);
        box-shadow: 0 12px 40px rgba(139, 92, 246, 0.25);
    }
    
    /* Valores das métricas - Roxo neon */
    div[data-testid="stMetricValue"] {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Labels - Cinza claro */
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }
    
    /* Delta */
    div[data-testid="stMetricDelta"] {
        color: #10b981;
        font-weight: 600;
    }
    
    /* Títulos */
    h1 {
        color: #ffffff;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    h2, h3 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.3px;
    }
    
    /* Subtítulos/Captions */
    .stCaption {
        color: rgba(255, 255, 255, 0.5) !important;
        font-size: 0.95rem;
    }
    
    /* Divisores invisíveis */
    hr {
        border: none;
        height: 2rem;
        background: transparent;
    }
    
    /* Botões roxos */
    .stButton button {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        border: none;
        color: white;
        font-weight: 600;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6);
    }
    
    /* Input de texto dark */
    .stTextInput input {
        background: rgba(30, 17, 57, 0.6);
        border: 1px solid rgba(139, 92, 246, 0.3);
        color: white;
        border-radius: 12px;
        padding: 0.75rem;
    }
    
    .stTextInput input::placeholder {
        color: rgba(255, 255, 255, 0.4);
    }
    
    .stTextInput input:focus {
        border-color: rgba(139, 92, 246, 0.8);
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
    }
    
    /* Slider roxo */
    .stSlider div[role="slider"] {
        background: #8b5cf6;
    }
    
    /* Tabela dark */
    .stDataFrame {
        background: rgba(30, 17, 57, 0.4);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 15px;
        overflow: hidden;
    }
    
    .stDataFrame thead tr th {
        background: rgba(139, 92, 246, 0.15) !important;
        color: #a78bfa !important;
        font-weight: 700;
        border: none !important;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 1px;
    }
    
    .stDataFrame tbody tr {
        background: rgba(30, 17, 57, 0.2);
        color: rgba(255, 255, 255, 0.85);
        border: none !important;
    }
    
    .stDataFrame tbody tr:hover {
        background: rgba(139, 92, 246, 0.1);
    }
    
    /* Gráficos com fundo escuro */
    .js-plotly-plot {
        background: rgba(30, 17, 57, 0.3) !important;
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 20px;
        padding: 1rem;
    }
    
    /* Scrollbar customizada */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(30, 17, 57, 0.3);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(139, 92, 246, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(139, 92, 246, 0.8);
    }
    
    /* Remove padding extra */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# ========== FUNÇÕES ==========
@st.cache_data(ttl=10)
def get_data():
    conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="job_market", user="user", password="password"
    )
    query = """
        SELECT 
            title, company, location, salary_min, job_url, is_anomaly, timestamp,
            CASE 
                WHEN is_anomaly THEN '🔥 Anomaly'
                WHEN salary_min > 0 THEN '✅ Active'
                ELSE '⚠️ No Info'
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

@st.cache_data(ttl=10)
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

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    refresh = st.slider("Auto-refresh interval", 5, 60, 15, help="Seconds")
    
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    search_term = st.text_input("🔍 Search jobs or companies")
    
    st.markdown("---")
    
    st.markdown("### 🛠️ Tech Stack")
    st.markdown("""
    • Apache Kafka  
    • Apache Spark  
    • PostgreSQL  
    • Streamlit  
    • Docker
    """)
    
    st.markdown("---")
    
    st.markdown("### 📊 Pipeline Status")
    st.success("🟢 **ONLINE**")
    st.caption(f"Refresh every {refresh}s")

# ========== DADOS ==========
try:
    stats = get_stats()
    df = get_data()
except Exception as e:
    st.error(f"❌ Database connection failed: {e}")
    st.stop()

if df.empty:
    st.warning("⚠️ Waiting for data stream...")
    st.stop()

if search_term:
    df = df[
        df['title'].str.contains(search_term, case=False, na=False) |
        df['company'].str.contains(search_term, case=False, na=False)
    ]

# ========== HEADER ==========
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("# 📊 Job Market Intelligence")
    st.caption("Real-Time Data Engineering Pipeline")
with col2:
    last_update = pd.Timestamp.now().strftime("%H:%M:%S")
    st.metric("🕐 Last Update", last_update)

st.markdown("<br>", unsafe_allow_html=True)

# ========== KPIS ==========
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Jobs", f"{int(stats['total'][0]):,}", help="Total job postings collected")

with col2:
    anomaly_pct = (int(stats['anomalies'][0]) / int(stats['total'][0]) * 100) if int(stats['total'][0]) > 0 else 0
    st.metric("Anomalies", int(stats['anomalies'][0]), delta=f"{anomaly_pct:.1f}%", delta_color="inverse", help="Jobs with unusual salary ranges")

with col3:
    avg_salary = float(stats['avg_salary'][0] or 0)
    st.metric("Avg Salary", f"${avg_salary:,.0f}", help="Average salary of jobs with salary data")

with col4:
    st.metric("Companies", int(stats['companies'][0]), help="Unique companies hiring")

st.markdown("<br>", unsafe_allow_html=True)

# ========== GRÁFICO PRINCIPAL - ÁREA SMOOTH ==========
st.markdown("### 📈 Market Trends")

df_timeline = df.groupby(df['event_date'].dt.date).agg({
    'salary_min': lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0,
    'title': 'count'
}).reset_index()
df_timeline.columns = ['date', 'avg_salary', 'count']

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_timeline['date'],
    y=df_timeline['avg_salary'],
    fill='tozeroy',
    fillcolor='rgba(139, 92, 246, 0.3)',
    line=dict(color='#8b5cf6', width=3, shape='spline', smoothing=1.3),
    mode='lines',
    name='Avg Salary',
    hovertemplate='<b>%{x}</b><br>Avg Salary: $%{y:,.0f}<extra></extra>'
))

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='rgba(255,255,255,0.8)', family='Inter'),
    height=280,
    margin=dict(l=20, r=20, t=20, b=20),
    xaxis=dict(
        showgrid=True,
        gridcolor='rgba(139, 92, 246, 0.1)',
        zeroline=False
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor='rgba(139, 92, 246, 0.1)',
        zeroline=False
    ),
    hovermode='x unified',
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========== GRID DE CARDS ==========
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 📊 Job Status")
    status_counts = df['status_vaga'].value_counts()
    
    fig = go.Figure(data=[
        go.Bar(
            y=status_counts.index,
            x=status_counts.values,
            orientation='h',
            marker=dict(
                color=['#ef4444', '#22c55e', '#f59e0b'],
                opacity=0.8
            ),
            text=status_counts.values,
            textposition='auto',
            textfont=dict(color='white', size=13, family='Inter', weight=600)
        )
    ])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(255,255,255,0.7)', family='Inter'),
        height=220,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False)
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 💰 Salary Data")
    labels = ['With Salary', 'No Data']
    values = [int(stats['with_salary'][0]), int(stats['no_salary'][0])]
    
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            marker=dict(colors=['#8b5cf6', '#374151']),
            textfont=dict(color='white', size=12, family='Inter')
        )
    ])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(255,255,255,0.8)', family='Inter'),
        height=220,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.markdown("#### 🏆 Top Company")
    top_company = df['company'].value_counts().head(1)
    
    if not top_company.empty:
        company_name = top_company.index[0]
        company_count = top_company.values[0]
        
        st.markdown(f"""
        <div style='text-align: center; padding: 2rem 0;'>
            <div style='font-size: 3rem; font-weight: 800; 
                        background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                {company_count}
            </div>
            <div style='color: rgba(255,255,255,0.6); font-size: 0.9rem; margin-top: 0.5rem; font-weight: 600;'>
                {company_name}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========== TOP EMPRESAS ==========
st.markdown("#### 🏢 Top 10 Companies")

top_companies = df['company'].value_counts().head(10)

fig = go.Figure(data=[
    go.Bar(
        y=top_companies.index,
        x=top_companies.values,
        orientation='h',
        marker=dict(
            color=top_companies.values,
            colorscale=[[0, '#6d28d9'], [0.5, '#8b5cf6'], [1, '#a78bfa']],
            showscale=False
        ),
        text=top_companies.values,
        textposition='auto',
        textfont=dict(color='white', size=12, family='Inter', weight=600)
    )
])

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='rgba(255,255,255,0.7)', family='Inter'),
    height=350,
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(showgrid=True, gridcolor='rgba(139, 92, 246, 0.1)', showticklabels=False),
    yaxis=dict(showgrid=False)
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========== TABELA ==========
st.markdown("#### 📋 Recent Job Postings")

st.dataframe(
    df[['title', 'company', 'location', 'salary_min', 'status_vaga', 'event_date', 'job_url']].head(20),
    column_config={
        "title": st.column_config.TextColumn("Job Title", width="large"),
        "company": st.column_config.TextColumn("Company", width="medium"),
        "location": st.column_config.TextColumn("Location", width="medium"),
        "salary_min": st.column_config.NumberColumn("Salary", format="$%.0f", width="small"),
        "status_vaga": st.column_config.TextColumn("Status", width="small"),
        "event_date": st.column_config.DatetimeColumn("Timestamp", format="DD/MM HH:mm"),
        "job_url": st.column_config.LinkColumn("Link", display_text="View")
    },
    use_container_width=True,
    hide_index=True,
    height=350
)

# ========== RODAPÉ ==========
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center; color: rgba(255,255,255,0.4); font-size: 0.85rem;'>
        ⚡ Real-Time Pipeline: Kafka • Spark • PostgreSQL<br>
        🚀 Data Engineering Portfolio Project © 2025
    </div>
    """, unsafe_allow_html=True)

# ========== AUTO-REFRESH ==========
time.sleep(refresh)
st.rerun()
