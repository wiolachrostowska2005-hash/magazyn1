import streamlit as st
import pandas as pd
from supabase import create_client
import time

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Lite", page_icon="🔹", layout="wide")

# --- 2. NOWY WYGLĄD (CSS) ---
st.markdown("""
    <style>
    /* TŁO APLIKACJI */
    .stApp { background-color: #ebf1f5; }
    
    /* PASEK BOCZNY */
    [data-testid="stSidebar"] {
        background-color: #004d40 !important;
        border-right: 1px solid #00332a;
    }
    
    /* GŁÓWNA KARTA */
    .main .block-container {
        background-color: #ffffff;
        padding: 2rem 3rem;
        border-radius: 15px;
        border: 1px solid #dce4e8;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-top: 1rem;
    }

    /* KOLORY TEKSTÓW */
    h1, h2, h3 { color: #004d40 !important; }
    p, div, span, label { color: #2c3e50; }
    
    /* Pasek boczny - tekst biały */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] div { color: #e0f2f1 !important; }

    /* Inputy */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
        color: #333333 !important;
        background-color: #f8f9fa !important;
        border: 1px solid #ced4da;
    }

    /* Ukrycie stopki */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. POŁĄCZENIE Z BAZĄ ---
try:
    # Obsługa sekretów (lokalnie i w chmurze)
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("⚠️ Brak pliku secrets.toml lub konfiguracji w Streamlit Cloud!")
    st.stop()

# --- 4. FUNKCJE ---
def pobierz_kategorie():
    """Pobiera listę kategorii do paska bocznego"""
    try:
        response = supabase.table('kategoria').select("id, nazwa").execute()
        return response.data
    except:
        return []

def pobierz_magazyn():
    """Pobiera produkty i łączy je z nazwą kategorii"""
    try:
        # Pobieramy wszystko z produktów + nazwę z połączonej tabeli kategoria
        response = supabase.table('produkty').select("*, kategoria(nazwa)").execute()
        dane = response.data
        
        if not dane:
            return pd.DataFrame()

        # Wyciąganie nazwy kategorii z zagnieżdżonego obiektu
        clean_data = []
        for row in dane:
            kat_info = row.get('kategoria')
            # Zabezpieczenie na wypadek usuniętej kategorii
            row['kategoria_nazwa'] = kat_info['nazwa'] if kat_info else "Brak"
            clean_data.append(row)
            
        return pd.DataFrame(clean_data)
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return pd.DataFrame()

# --- 5. GŁÓWNA APLIKACJA ---
def main():
    col1, col2 = st.columns([1, 15])
    with col1: st.write("# 🔹")
    with col2:
        st.title("System Magazynowy")
        st.caption("Panel Supabase (Cloud)")

    st.divider()

    # --- PANEL BOCZNY (DODAWANIE) ---
    with st.sidebar:
        st.header("➕ Nowy towar")
        
        # Pobieranie kategorii z bazy
        lista_kat = pobierz_kategorie()
        
        if not lista_kat:
            st.warning("⚠️ Brak kategorii w bazie! Dodaj je najpierw w Supabase.")
            mapa_kat = {}
        else:
            # Tworzymy mapę {Nazwa Kategorii: ID Kategorii}
            mapa_kat = {k['nazwa']: k['id'] for k in lista_kat}

        with st.form("add_form", clear_on_submit=True):
            nazwa = st.text_input("Nazwa produktu")
            
            # Selectbox z kategoriami
            if mapa_kat:
                wybrana_kat = st.selectbox("Kategoria", list(mapa_kat.keys()))
            else:
                wybrana_kat = None

            c1, c2 = st.columns(2)
            with c1: ilosc = st.number_input("Ilość", min_value=1, value=10)
            with c2: cena = st.number_input("Cena (PLN)", min_value=0.00, step=0.01)

            submitted = st.form_submit_button("Zapisz", type="primary")
            
            if submitted:
                if nazwa and wybrana_kat:
                    try:
                        # Przygotowanie danych do wysyłki
                        nowy_towar = {
                            "nazwa": nazwa,
                            "liczba": ilosc,
                            "cena": cena,
                            "kategoria_id": mapa_kat[wybrana_kat] # Kluczowe dla relacji!
                        }
                        supabase.table('produkty').insert(nowy_towar).execute()
                        st.success("✅ Dodano!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd zapisu: {e}")
                else:
                    st.warning("Uzupełnij nazwę i kategorię.")

    # --- TABELA GŁÓWNA ---
    df = pobierz_magazyn()

    if not df.empty:
        # Metryki
        total_items = df['liczba'].sum()
        total_val = (df['liczba'] * df['cena']).sum() if 'cena' in df.columns else 0
        
        m1, m2 = st.columns(2)
        m1.metric("📦 Stan Magazynowy", f"{total_items}", "sztuk")
        m2.metric("💰 Wartość", f"{total_val:,.2f} PLN".replace(",", " "), "PLN")
        
        st.write("")
        st.subheader("📋 Lista asortymentu")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_order=["id", "nazwa", "kategoria_nazwa", "liczba", "cena"],
            column_config={
                "id": st.column_config.TextColumn("ID", width="small"),
                "nazwa": st.column_config.TextColumn("Produkt", width="medium"),
                "kategoria_nazwa": st.column_config.TextColumn("Kategoria", width="medium"),
                "liczba": st.column_config.ProgressColumn("Stan", format="%d", max_value=max(df['liczba'].max(), 100)),
                "cena": st.column_config.NumberColumn("Cena", format="%.2f zł")
            }
        )
        
        # Usuwanie
        st.divider()
        with st.expander("🗑️ Usuń pozycję"):
            c1, c2 = st.columns([3,1])
            with c1:
                opcje = df.apply(lambda x: f"ID {x['id']}: {x['nazwa']}", axis=1)
                wybrany = st.selectbox("Wybierz", opcje, label_visibility="collapsed")
            with c2:
                if st.button("Usuń trwale"):
                    id_del = int(wybrany.split("ID ")[1].split(":")[0])
                    supabase.table('produkty').delete().eq('id', id_del).execute()
                    st.success("Usunięto!")
                    time.sleep(0.5)
                    st.rerun()
    else:
        st.info("Magazyn pusty. Dodaj towar w pasku po lewej.")

if __name__ == "__main__":
    main()
