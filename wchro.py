import streamlit as st
import pandas as pd
from supabase import create_client
import time

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Prosty Magazyn", page_icon="🏢", layout="wide")

# --- 2. NOWY WYGLĄD (MOTYW GRANATOWY) ---
st.markdown("""
    <style>
    /* Tło całej aplikacji - Bardzo jasny szary, czysty */
    .stApp {
        background-color: #f4f6f9;
    }

    /* Pasek boczny - Profesjonalny Granat (Midnight Blue) */
    [data-testid="stSidebar"] {
        background-color: #2c3e50 !important;
    }

    /* Karta główna - Biała z cieniem */
    .main .block-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-top: 1rem;
    }

    /* --- TEKSTY --- */
    /* Główne nagłówki - Ciemny granat */
    h1, h2, h3 {
        color: #2c3e50 !important;
    }
    
    /* Tekst w Sidebarze - Biały/Szary */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #ecf0f1 !important;
    }

    /* Ukrycie stopki i menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Inputy - Klasyczne białe */
    .stTextInput input, .stNumberInput input {
        color: #2c3e50 !important;
        background-color: #ffffff !important;
        border: 1px solid #bdc3c7;
    }

    /* --- METRYKI (LICZNIKI) --- */
    /* Kolor akcentowy - Pomarańczowy (Carrot Orange) */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #e67e22 !important; 
    }
    
    [data-testid="stMetricLabel"] {
        color: #7f8c8d !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. POŁĄCZENIE Z BAZĄ ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("⚠️ Błąd połączenia! Brakuje pliku .streamlit/secrets.toml")
    st.stop()

# --- 4. FUNKCJE (TYLKO MAGAZYN, BEZ HISTORII) ---
def pobierz_magazyn():
    """Pobiera dane tylko z tabeli produkty"""
    response = supabase.table('produkty').select("*").execute()
    return pd.DataFrame(response.data)

# --- 5. GŁÓWNA APLIKACJA ---
def main():
    # --- NAGŁÓWEK ---
    col1, col2 = st.columns([1, 15])
    with col1:
        st.write("# 🏢")
    with col2:
        st.title("System Magazynowy Lite")
        st.caption("Prosta ewidencja towarów (Supabase)")

    st.divider()

    # --- SIDEBAR (DODAWANIE) ---
    with st.sidebar:
        st.header("➕ Dodaj towar")
        st.write("Wprowadź dane do systemu:")
        
        with st.form("add_form", clear_on_submit=True):
            # Inputy wyglądają klasycznie
            nazwa = st.text_input("Nazwa produktu")
            col_sb1, col_sb2 = st.columns(2)
            with col_sb1:
                ilosc = st.number_input("Ilość", min_value=1, value=10)
            with col_sb2:
                # Strzałki do groszy (step=0.01)
                cena = st.number_input("Cena (PLN)", min_value=0.00, value=0.00, step=0.01)

            # Przycisk
            submitted = st.form_submit_button("Zapisz w bazie", type="primary")
            
            if submitted:
                if nazwa:
                    # Prosty słownik, bez logów
                    dane = {"nazwa": nazwa, "liczba": ilosc, "cena": cena}
                    try:
                        supabase.table('produkty').insert(dane).execute()
                        st.success("✅ Gotowe!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                else:
                    st.warning("⚠️ Podaj nazwę!")

        st.markdown("---")
        st.info("Wersja uproszczona (Bez Historii)")

    # --- DASHBOARD ---
    try:
        df = pobierz_magazyn()
        
        if not df.empty:
            # Standaryzacja nazw kolumn na małe litery
            df.columns = [c.lower() for c in df.columns]
            
            # Proste KPI
            total_items = df['liczba'].sum()
            total_val = (df['liczba'] * df['cena']).sum() if 'cena' in df.columns else 0

            # Wyświetlanie liczników
            m1, m2 = st.columns(2)
            m1.metric("📦 Stan Magazynowy", f"{total_items}", "sztuk")
            m2.metric("💰 Wartość Towarów", f"{total_val:,.2f} PLN".replace(",", " "), "szacunkowa")
            
            st.markdown("### 📋 Lista produktów")
            
            # Tabela
            st.dataframe(
                df[['id', 'nazwa', 'liczba', 'cena']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.TextColumn("ID", width="small"),
                    "nazwa": st.column_config.TextColumn("Produkt", width="large"),
                    "liczba": st.column_config.ProgressColumn(
                        "Ilość", 
                        format="%d", 
                        max_value=max(df['liczba']) * 1.1,
                        min_value=0
                    ),
                    "cena": st.column_config.NumberColumn("Cena", format="%.2f zł")
                }
            )

            # Sekcja Usuwania (bez zakładek, po prostu pod spodem)
            st.divider()
            with st.expander("🗑️ Usuń towar"):
                if 'id' in df.columns:
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        # Lista do wyboru
                        opcje = df.apply(lambda x: f"ID {x['id']}: {x['nazwa']}", axis=1)
                        wybrany = st.selectbox("Wybierz produkt", opcje, label_visibility="collapsed")
                    with c2:
                        if st.button("Usuń trwale"):
                            id_del = int(wybrany.split("ID ")[1].split(":")[0])
                            # Tylko usuwamy, nie zapisujemy historii
                            supabase.table('produkty').delete().eq('id', id_del).execute()
                            st.rerun()

        else:
            st.info("Baza jest pusta. Dodaj pierwszy produkt w menu po lewej.")

    except Exception as e:
        st.error("Problem z połączeniem.")
        with st.expander("Szczegóły"):
            st.write(e)

if _name_ == "_main_":
    main()
