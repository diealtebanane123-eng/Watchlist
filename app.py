import streamlit as st
import yfinance as yf
import pandas as pd

# App-Titel & Styling
st.set_page_config(page_title="Meine Monats-Watchlist", layout="wide")
st.title("📈 Meine Watchlist: Fokus auf Monatstrends")
st.write("Diese App zeigt dir standardmäßig die Performance der letzten 30 Tage.")

# 1. Watchlist-Datenbank im Hintergrund (Session State)
if "watchlist" not in st.session_state:
    # Ein paar Standard-Ticker zum Start (Apple, Microsoft, Tesla, SAP)
    st.session_state.watchlist = ["AAPL", "MSFT", "TSLA", "SAP.DE"]

# 2. Sidebar für die Verwaltung
with st.sidebar:
    st.header("⚙️ Watchlist verwalten")
    neuer_ticker = st.text_input("Ticker-Symbol hinzufügen (z.B. AMZN, BABA):").upper()
    if st.button("Hinzufügen") and neuer_ticker:
        if neuer_ticker not in st.session_state.watchlist:
            st.session_state.watchlist.append(neuer_ticker)
            st.success(f"{neuer_ticker} hinzugefügt!")
        else:
            st.warning("Ticker existiert bereits.")
            
    entfernen_ticker = st.selectbox("Ticker entfernen:", st.session_state.watchlist)
    if st.button("Entfernen"):
        st.session_state.watchlist.remove(entfernen_ticker)
        st.success(f"{entfernen_ticker} entfernt!")

# 3. Daten von Yahoo Finance abrufen und verarbeiten
data_list = []

if st.session_state.watchlist:
    with st.spinner("Lade aktuelle Monatstrends..."):
        for ticker in st.session_state.watchlist:
            try:
                # Wir holen die Daten der letzten 3 Monate, um den Monatsverlauf sauber zu berechnen
                stock = yf.Ticker(ticker)
                hist = stock.history(period="3mo")
                
                if len(hist) >= 20: # Sicherstellen, dass genug Handelstage da sind
                    aktueller_kurs = hist["Close"].iloc[-1]
                    kurs_vor_monat = hist["Close"].iloc[-20] # ca. 20 Handelstage = 1 Monat
                    kurs_vor_tag = hist["Close"].iloc[-2] # Letzter Schlusskurs für Tagestrend
                    
                    # Trends berechnen
                    monatstrend_prozent = ((aktueller_kurs - kurs_vor_monat) / kurs_vor_monat) * 100
                    tagestrend_prozent = ((aktueller_kurs - kurs_vor_tag) / kurs_vor_tag) * 100
                    
                    # Name des Unternehmens holen
                    name = stock.info.get("longName", ticker)
                    
                    data_list.append({
                        "Ticker": ticker,
                        "Name": name,
                        "Aktueller Kurs ($/€)": round(aktueller_kurs, 2),
                        "Tagestrend (%)": round(tagestrend_prozent, 2),
                        "Monatstrend (%)": round(monatstrend_prozent, 2)
                    })
            except Exception as e:
                st.error(f"Fehler beim Laden von {ticker}: {e}")

    # 4. Daten anzeigen
    if data_list:
        df = pd.DataFrame(data_list)
        
        # Sortierung standardmäßig nach dem besten Monatstrend
        df = df.sort_values(by="Monatstrend (%)", ascending=False)
        
        # Formatierung für die Tabelle (Grün für Plus, Rot für Minus)
        def color_trend(val):
            color = 'green' if val > 0 else 'red'
            return f'color: {color}; font-weight: bold;'
        
        # Tabelle stylen und anzeigen
        styled_df = df.style.map(color_trend, subset=["Tagestrend (%)", "Monatstrend (%)"])
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Kleine visuelle Kacheln für die Top-Monats-Performer
        st.subheader("🔥 Top 3 Performer diesen Monat")
        cols = st.columns(3)
        for i, row in enumerate(data_list[:3]):
            if i < len(cols):
                cols[i].metric(
                    label=row["Name"], 
                    value=f"{row['Aktueller Kurs ($/€)']} €/$", 
                    delta=f"{row['Monatstrend (%)']}% (1M)"
                )
else:
    st.info("Deine Watchlist ist leer. Füge in der Sidebar Aktien hinzu!")
