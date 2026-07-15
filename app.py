import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
import re

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Asset Intelligence Watchlist 2.0",
    page_icon="📈",
    layout="wide"
)

# Custom Styling für einen modernen Look
st.markdown("""
    <style>
    .metric-box {
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Asset Intelligence Watchlist 2.0")
st.markdown("Verfolge die Live-Performance deiner Assets mit automatischer ISIN-Suche und Firmenlogos.")

# --- DATEN-STRUKTUR (WATCHLIST IM SPEICHER INITIALISIEREN) ---
# Wir speichern nun strukturierte Dictionaries, um Ticker, Klarnamen und Logos dauerhaft zu sichern
if "watchlist" not in st.session_state:
    st.session_state.watchlist = [
        {
            "symbol": "AAPL", 
            "name": "Apple Inc.", 
            "logo": "https://www.google.com/s2/favicons?sz=128&domain=apple.com"
        },
        {
            "symbol": "BTC-USD", 
            "name": "Bitcoin USD", 
            "logo": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"
        },
        {
            "symbol": "MSFT", 
            "name": "Microsoft Corporation", 
            "logo": "https://www.google.com/s2/favicons?sz=128&domain=microsoft.com"
        },
        {
            "symbol": "SAP.DE", 
            "name": "SAP SE", 
            "logo": "https://www.google.com/s2/favicons?sz=128&domain=sap.com"
        }
    ]

# --- HILFSFUNKTIONEN ---
def is_isin(query):
    """Prüft, ob der eingegebene Text dem Format einer ISIN entspricht (12 Zeichen, startet mit Länderkürzel)"""
    return bool(re.match(r"^[A-Z]{2}[A-Z0-9]{9}\d$", query.upper().strip()))

def get_logo_url(symbol, info):
    """Generiert eine passende Logo-URL für Aktien (via Google Favicon) oder Krypto (via CoinGecko)"""
    # Krypto-Check
    if "-USD" in symbol or "-EUR" in symbol:
        crypto_symbol = symbol.split("-")[0].upper()
        common_cryptos = {
            "BTC": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
            "ETH": "https://assets.coingecko.com/coins/images/279/large/ethereum.png",
            "SOL": "https://assets.coingecko.com/coins/images/4128/large/solana.png",
            "XRP": "https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-branded.png",
            "ADA": "https://assets.coingecko.com/coins/images/975/large/cardano.png",
            "DOT": "https://assets.coingecko.com/coins/images/12171/large/polkadot.png",
            "DOGE": "https://assets.coingecko.com/coins/images/325/large/dogecoin.png"
        }
        return common_cryptos.get(crypto_symbol, "https://assets.coingecko.com/coins/images/1/large/bitcoin.png")
    
    # Aktien & ETFs via Website Favicon
    website = info.get("website")
    if website:
        domain = urllib.parse.urlparse(website).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return f"https://www.google.com/s2/favicons?sz=128&domain={domain}"
    
    # Fallback
    return "https://www.google.com/s2/favicons?sz=128&domain=yahoo.com"


# --- SIDEBAR: ASSETS VERWALTEN (SUCHE) ---
with st.sidebar:
    st.header("⚙️ Watchlist verwalten")
    
    user_input = st.text_input(
        "Ticker-Symbol oder ISIN eingeben:",
        placeholder="z.B. AAPL, DE0007164600, BTC-USD"
    ).strip().upper()
    
    if st.button("Asset hinzufügen", use_container_width=True):
        if user_input:
            with st.spinner("Prüfe Asset und lade Details..."):
                symbol_to_add = None
                resolved_name = None
                
                # Fall 1: Eingabe ist eine ISIN
                if is_isin(user_input):
                    st.info(f"🔎 ISIN '{user_input}' erkannt. Suche Ticker-Symbol...")
                    try:
                        search_result = yf.Search(user_input, max_results=1)
                        if search_result.quotes:
                            quote = search_result.quotes[0]
                            symbol_to_add = quote.get("symbol")
                            resolved_name = quote.get("shortname") or quote.get("longname") or symbol_to_add
                        else:
                            st.error("ISIN konnte bei Yahoo Finance nicht aufgelöst werden.")
                    except Exception as e:
                        st.error(f"Fehler bei der ISIN-Suche: {e}")
                
                # Fall 2: Eingabe ist ein normales Ticker-Symbol
                else:
                    symbol_to_add = user_input
                
                # Prüfen, ob das Asset bereits existiert
                if symbol_to_add:
                    already_exists = any(item["symbol"] == symbol_to_add for item in st.session_state.watchlist)
                    
                    if already_exists:
                        st.warning(f"Das Asset '{symbol_to_add}' ist bereits in deiner Watchlist.")
                    else:
                        try:
                            # Test-Abfrage zur Validierung
                            ticker = yf.Ticker(symbol_to_add)
                            hist = ticker.history(period="1d")
                            
                            if not hist.empty:
                                info = ticker.info
                                if not resolved_name:
                                    resolved_name = info.get("longName") or info.get("shortName") or symbol_to_add
                                
                                logo_url = get_logo_url(symbol_to_add, info)
                                
                                # In Watchlist speichern
                                st.session_state.watchlist.append({
                                    "symbol": symbol_to_add,
                                    "name": resolved_name,
                                    "logo": logo_url
                                })
                                st.success(f"Erfolgreich hinzugefügt:\n**{resolved_name}** ({symbol_to_add})")
                                st.rerun()
                            else:
                                st.error("Keine Preisdaten für dieses Kürzel verfügbar.")
                        except Exception as e:
                            st.error(f"Asset konnte nicht validiert werden: {e}")
        else:
            st.warning("Bitte gib ein Symbol oder eine ISIN ein.")
            
    st.write("---")
    
    # Asset entfernen
    if st.session_state.watchlist:
        # Erstelle Liste mit Namen für das Dropdown
        remove_options = {f"{item['name']} ({item['symbol']})": item for item in st.session_state.watchlist}
        selected_to_remove_label = st.selectbox("Asset entfernen:", list(remove_options.keys()))
        
        if st.button("Aus Watchlist löschen", use_container_width=True):
            item_to_remove = remove_options[selected_to_remove_label]
            st.session_state.watchlist.remove(item_to_remove)
            st.success(f"'{item_to_remove['name']}' wurde entfernt.")
            st.rerun()
    else:
        st.info("Deine Watchlist ist leer.")


# --- PREISDATEN LIVE ABRUFEN ---
@st.cache_data(ttl=30) # 30 Sekunden Cache für schnellen Refresh
def fetch_prices_for_watchlist(symbols):
    price_results = {}
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="3mo")
            if hist.empty:
                continue
            
            current_price = hist['Close'].iloc[-1]
            
            # Performance-Berechnungen
            daily_perf, weekly_perf, monthly_perf = 0.0, 0.0, 0.0
            
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                daily_perf = ((current_price - prev_close) / prev_close) * 100
            if len(hist) >= 6:
                weekly_close = hist['Close'].iloc[-6]
                weekly_perf = ((current_price - weekly_close) / weekly_close) * 100
            if len(hist) >= 22:
                monthly_close = hist['Close'].iloc[-22]
                monthly_perf = ((current_price - monthly_close) / monthly_close) * 100
                
            price_results[sym] = {
                "Preis": current_price,
                "Tag": daily_perf,
                "Woche": weekly_perf,
                "Monat": monthly_perf
            }
        except Exception:
            pass
    return price_results


# --- MAIN PANEL ---
if st.session_state.watchlist:
    symbols = [item["symbol"] for item in st.session_state.watchlist]
    
    with st.spinner("Lade Live-Preise..."):
        prices = fetch_prices_for_watchlist(symbols)
    
    # DataFrame für die Anzeige aufbauen
    display_rows = []
    for item in st.session_state.watchlist:
        sym = item["symbol"]
        if sym in prices:
            display_rows.append({
                "Logo": item["logo"],
                "Name": item["name"],
                "Ticker": sym,
                "Preis": prices[sym]["Preis"],
                "Täglich (%)": prices[sym]["Tag"],
                "Wöchentlich (%)": prices[sym]["Woche"],
                "Monatlich (%)": prices[sym]["Monat"]
            })
            
    if display_rows:
        df = pd.DataFrame(display_rows)
        
        # --- HIGHLIGHT METRICS (TOP GEWINNER / VERLIERER) ---
        col1, col2, col3 = st.columns(3)
        
        # Berechne Top-Performer des Tages
        top_gainer = df.loc[df['Täglich (%)'].idxmax()]
        top_loser = df.loc[df['Täglich (%)'].idxmin()]
        
        with col1:
            st.markdown(f"""
                <div class='metric-box'>
                    <h5 style='margin:0; color:#64748b;'>🔥 Top Gewinner (Heute)</h5>
                    <h3 style='margin:5px 0; color:#2ecc71;'>{top_gainer['Name']}</h3>
                    <p style='margin:0; font-weight:bold; color:#2ecc71;'>{top_gainer['Täglich (%)']:+.2f}%</p>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class='metric-box'>
                    <h5 style='margin:0; color:#64748b;'>❄️ Stärkster Verlierer (Heute)</h5>
                    <h3 style='margin:5px 0; color:#e74c3c;'>{top_loser['Name']}</h3>
                    <p style='margin:0; font-weight:bold; color:#e74c3c;'>{top_loser['Täglich (%)']:+.2f}%</p>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class='metric-box'>
                    <h5 style='margin:0; color:#64748b;'>💼 Überwachte Assets</h5>
                    <h3 style='margin:5px 0; color:#1e3a8a;'>{len(df)}</h3>
                    <p style='margin:0; color:#64748b;'>in deiner Watchlist</p>
                </div>
            """, unsafe_allow_html=True)
            
        st.write("---")
        st.subheader("📋 Live-Watchlist")
        
        # Performance-Färbung (Grün/Rot) via Pandas Styling
        def color_performance(val):
            if isinstance(val, (int, float)):
                color = '#2ecc71' if val >= 0 else '#e74c3c'
                return f'color: {color}; font-weight: bold;'
            return ''
            
        styled_df = df.style.format({
            "Preis": "{:.2f} €",
            "Täglich (%)": "{:+.2f}%",
            "Wöchentlich (%)": "{:+.2f}%",
            "Monatlich (%)": "{:+.2f}%"
        }).map(color_performance, subset=["Täglich (%)", "Wöchentlich (%)", "Monatlich (%)"])
        
        # Tabelle rendern mit Image-Spalte für die Logos
        st.dataframe(
            styled_df,
            column_config={
                "Logo": st.column_config.ImageColumn("Logo", width="small"),
                "Name": st.column_config.TextColumn("Asset Name", width="medium"),
                "Ticker": st.column_config.TextColumn("Kürzel", width="small"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        # --- DETAIL-CHART ---
        st.write("---")
        st.subheader("📊 Interaktiver Detail-Chart")
        selected_asset_label = st.selectbox(
            "Wähle ein Asset aus deiner Watchlist:",
            [f"{item['name']} ({item['symbol']})" for item in st.session_state.watchlist]
        )
        
        # Gewählten Ticker extrahieren
        selected_ticker = re.search(r"\((.*?)\)", selected_asset_label).group(1)
        
        chart_period = st.segmented_control(
            "Zeitraum für den Chart:",
            options=["1mo", "3mo", "1y", "5y"],
            default="3mo"
        )
        
        if selected_ticker:
            with st.spinner("Lade Chart-Daten..."):
                chart_data = yf.Ticker(selected_ticker).history(period=chart_period)
                if not chart_data.empty:
                    st.line_chart(chart_data['Close'], use_container_width=True)
                else:
                    st.warning("Keine Chart-Daten für diesen Zeitraum verfügbar.")
                    
    else:
        st.error("Es konnten keine Daten für deine Watchlist geladen werden.")
else:
    st.info("Füge in der linken Seitenleiste ein Asset hinzu, um dein Dashboard zu starten!")