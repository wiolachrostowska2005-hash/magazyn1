import streamlit as st
import pandas as pd
from supabase import create_client
import time

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Lite", page_icon="🔹", layout="wide")

# --- 2. NOWY WYGLĄD (MORSKI / TEAL) ---
st.markdown("""
    <style>
    /* Tło całej aplikacji - Czysta biel */
    .stApp {
        background-color: #ffffff;
    }

    /* Pasek boczny - Ciemny turkus (Teal) */
    [data-testid="stSidebar"] {
        background-color: #004d40 !important;
    }

    /* Karta główna - Delikatny szary z ramką */
    .main .block-container {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* --- KOLORY TEKSTÓW --- */
    h1, h2, h3 {
        color: #00695c !important; /* Ciemny morski dla nagłówków */
    }
    
    /* Teksty w Sidebarze - Białe */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #e0f2f1 !important;
    }

    /* Ukrycie elementów Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Inputy - Białe z turkusowym obramowaniem przy aktywności */
    .stTextInput input, .stNumberInput input {
        color: #333333 !important;
        background-color: #ffffff !important;
        border: 1px solid #b2dfdb;
    }

    /* --- METRYKI --- */
    /* Liczby w kolorze morskim */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00796b !important; 
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

# --- 4. FUNKCJE (TYLKO ODCZYT PRODUKTÓW) ---
def pobierz_magazyn():
    # Pobieramy tylko produkty, bez historii
    response = supabase.table('produkty').select("*").execute()
    return pd.DataFrame(response.data)

# --- 5. GŁÓWNA APLIKACJA ---
def main():
    # --- NAGŁÓWEK ---
    col1, col2 = st.columns([1, 15])
    with col1:
        st.write("# 🔹")
    with col2:
        st.title("System Magazynowy")
        st.caption("Wersja Lite (Bez historii operacji)")

    st.divider()

    # --- SIDEBAR (DODAWANIE) ---
    with st.sidebar:
        st.header("➕ Nowy towar")
        
        with st.form("add_form", clear_on_submit=True):
            nazwa = st.text_input("Nazwa produktu")
            col_sb1, col_sb2 = st.columns(2)
            with col_sb1:
                ilosc = st.number_input("Ilość", min_value=1, value=10)
            with col_sb2:
                cena = st.number_input("Cena (PLN)", min_value=0.00, value=0.00, step=0.01)

            # Przycisk
            submitted = st.form_submit_button("Zapisz", type="primary")
            
            if submitted:
                if nazwa:
                    # Tworzymy prosty obiekt (tylko to, co jest w tabeli produkty)
                    dane = {
                        "nazwa": nazwa, 
                        "liczba": ilosc, 
                        "cena": cena
                    }
                    try:
                        supabase.table('produkty').insert(dane).execute()
                        st.success("✅ Dodano!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd bazy: {e}")
                else:
                    st.warning("⚠️ Podaj nazwę!")

    # --- DASHBOARD ---
    try:
        df = pobierz_magazyn()
        
        if not df.empty:
            # Zamiana na małe litery dla pewności
            df.columns = [c.lower() for c in df.columns]
            
            # KPI
            total_items = df['liczba'].sum()
            total_val = (df['liczba'] * df['cena']).sum() if 'cena' in df.columns else 0

            # Liczniki
            m1, m2 = st.columns(2)
            m1.metric("📦 Stan Magazynowy", f"{total_items}", "sztuk")
            m2.metric("💰 Wartość", f"{total_val:,.2f} PLN".replace(",", " "), "PLN")
            
            st.write("")
            st.subheader("📋 Lista asortymentu")
            
            # Tabela
            st.dataframe(
                df[['id', 'nazwa', 'liczba', 'cena']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.TextColumn("ID", width="small"),
                    "nazwa": st.column_config.TextColumn("Produkt", width="large"),
                    "liczba": st.column_config.ProgressColumn(
                        "Stan", 
                        format="%d", 
                        max_value=max(df['liczba']) * 1.2,
                        min_value=0
                    ),
                    "cena": st.column_config.NumberColumn("Cena", format="%.2f zł")
                }
            )

            # Proste usuwanie pod tabelą
            with st.expander("🗑️ Usuń pozycję"):
                if 'id' in df.columns:
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        opcje = df.apply(lambda x: f"ID {x['id']}: {x['nazwa']}", axis=1)
                        wybrany = st.selectbox("Wybierz", opcje, label_visibility="collapsed")
                    with c2:
                        if st.button("Usuń trwale"):
                            id_del = int(wybrany.split("ID ")[1].split(":")[0])
                            # Usuwamy tylko z produktów
                            supabase.table('produkty').delete().eq('id', id_del).execute()
                            st.rerun()

        else:
            st.info("Magazyn pusty. Dodaj coś w menu po lewej.")

    except Exception as e:
        st.error("Problem z połączeniem.")
        with st.expander("Szczegóły"):
            st.write(e)
