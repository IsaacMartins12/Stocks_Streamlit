import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="Macro Stock Dashboard", layout="wide")

# Estilo global
st.markdown("<h1 style='text-align: center;'>📊 Macro Stock Dashboard</h1><br>", unsafe_allow_html=True)
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-size: 18px;
        }

        h1 {
            font-size: 36px !important;
            font-weight: bold;
        }

        .stMetric label {
            font-size: 20px !important;
        }

        .stMetric div {
            font-size: 26px !important;
        }

        .stDownloadButton > button {
            font-size: 18px !important;
        }
    </style>
""", unsafe_allow_html=True)


class Stocks:

    def __init__(self, tickers, start_date, end_date, show_ma=False, ma_window=20):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.show_ma = show_ma
        self.ma_window = ma_window
        self.df_final = pd.DataFrame()

    def fetch_data(self):
        self.df_final = fetch_yfinance_data(
            self.tickers,
            self.start_date,
            self.end_date,
            self.show_ma,
            self.ma_window
        )

    def show_metrics(self):
        col1, col2 = st.columns(2)
        with col1:
            for ticker in self.tickers:
                try:
                    last_price = self.df_final[self.df_final["Ticker"] == ticker]["Close"].dropna().iloc[-1]
                    st.metric(f"{ticker} - Preço Atual", f"R$ {last_price:.2f}")
                except:
                    st.warning(f"Preço não encontrado para {ticker}.")
        with col2:
            for ticker in self.tickers:
                try:
                    series = self.df_final[self.df_final["Ticker"] == ticker]["Close"].dropna()
                    variation = ((series.iloc[-1] - series.iloc[0]) / series.iloc[0]) * 100
                    st.metric(f"{ticker} - Variação no Período", f"{variation:.2f}%", delta=f"{variation:.2f}%")
                except:
                    pass

    def plot_graphs(self, selected_ticker):
        df = self.df_final[self.df_final["Ticker"] == selected_ticker]

        # Preço
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode='lines', name="Preço", line=dict(color='cyan')))
        if self.show_ma:
            fig_price.add_trace(go.Scatter(x=df["Date"], y=df["MA"], mode='lines', name=f"Média {self.ma_window}D", line=dict(color='orange')))
        fig_price.update_layout(title=f"💹 Histórico de Preço - {selected_ticker}", template="plotly_dark", xaxis_title="Data", yaxis_title="Preço (R$)", height=500)

        # Volume
        fig_volume = px.bar(df, x="Date", y="Volume", title=f"📦 Volume Negociado - {selected_ticker}", template="plotly_dark", labels={"Volume": "Volume (ações)"})
        fig_volume.update_layout(height=300)

        st.plotly_chart(fig_price, use_container_width=True)
        st.plotly_chart(fig_volume, use_container_width=True)

    def export_data(self):
        csv = self.df_final.to_csv(index=False).encode('utf-8')
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            self.df_final.to_excel(writer, index=False, sheet_name='Histórico')
        xlsx_data = output.getvalue()

        col_csv, col_excel = st.columns(2)
        with col_csv:
            st.download_button("⬇️ CSV", data=csv, file_name="dados_acoes.csv", mime="text/csv")
        with col_excel:
            st.download_button("⬇️ Excel", data=xlsx_data, file_name="dados_acoes.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")



@st.cache_data(ttl=30)
def fetch_yfinance_data(tickers, start_date, end_date, show_ma=False, ma_window=20):
    raw_data = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        group_by='ticker',
        progress=False
    )

    df_list = []
    for ticker in tickers:
        try:
            df = raw_data[ticker].reset_index()
            df["Ticker"] = ticker
            if show_ma:
                df["MA"] = df["Close"].rolling(window=ma_window).mean()
            df_list.append(df)
        except Exception:
            st.warning(f"Erro ao carregar dados para {ticker}.")
    return pd.concat(df_list, ignore_index=True)


# 🧾 Inputs via Sidebar
with st.sidebar:
    st.header("🔎 Configurações")
    tickers_input = st.text_input("Ativos (separados por vírgula)", "PETR4.SA,VALE3.SA,ITUB4.SA")
    start_date = st.date_input("Data inicial", pd.to_datetime("2020-01-01"))
    end_date = st.date_input("Data final", pd.to_datetime("2025-01-01"))
    show_ma = st.checkbox("Mostrar Médias Móveis", value=True)
    ma_window = st.slider("Período da Média Móvel (dias)", 5, 100, 20) if show_ma else 20
    st.markdown("----")

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# 🧠 Executar aplicação
try:
    stock_app = Stocks(tickers, start_date, end_date, show_ma, ma_window)
    stock_app.fetch_data()
    stock_app.show_metrics()

    st.markdown("---")
    selected_ticker = st.selectbox("📌 Selecione o ativo para análise detalhada", tickers)
    stock_app.plot_graphs(selected_ticker)

    st.markdown("### 📥 Exportar dados")
    stock_app.export_data()

except Exception as e:
    st.error(f"Ocorreu um erro ao processar os dados: {e}")
