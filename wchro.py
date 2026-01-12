import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import time

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn", page_icon="📦", layout="wide")

# --- 2. CSS - DARK MODE ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #333; }
    .main .block-container { background-color: #1f2937; padding: 2rem 3rem; border-radius: 15px; margin-top: 1rem; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, .stMarkdown { color: #e5e7eb !important; }
    button p { color: inherit !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stTextInput input, .stNumberInput input { color: #ffffff !important; background-color: #374151 !important; border: 1px solid #4b5563; }
    .stTextInput label, .stNumberInput label { color: #9ca3af !important; }
    [data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 700; color: #60a5fa !important; }
    [data-testid="stMetricLabel"] { color: #9ca3af !important; }
    [data-testid="stDataFrame"] { background-color: #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. POŁĄCZENIE Z BAZĄ ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("⚠️ Błąd połączenia! Sprawdź plik .streamlit/secrets.toml")
    st.stop()

# --- 4. FUNKCJE ---
def pobierz_magazyn():
    response = supabase.table('produkty').select("*").execute()
    return pd.DataFrame(response.data)

def dodaj_log(produkt, akcja, ilosc):
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M")
    dane = {"data": teraz, "produkt": produkt, "akcja": akcja, "ilosc": ilosc}
    try:
        supabase.table('historia').insert(dane).execute()
    except Exception as e:
        print(f"Brak tabeli historia lub błąd zapisu: {e}")

# --- 5. GŁÓWNA APLIKACJA ---
def main():
    # --- NAGŁÓWEK ---
    col_logo, col_title = st.columns([1, 10])
    with col_logo: st.markdown("# 📦")
    with col_title:
        st.title("Magazyn")
        st.caption("System zarządzania stanem (Supabase Cloud)")

    st.divider()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🛠️ Panel Operacyjny")
        
        with st.form("dodawanie_form", clear_on_submit=True):
            nazwa_input = st.text_input("Nazwa produktu", placeholder="np. Opony Zimowe")
            c1, c2 = st.columns(2)
            with c1: liczba_input = st.number_input("Ilość szt.", min_value=1, value=10, step=1)
            with c2: cena_input = st.number_input("Cena jedn. (PLN)", min_value=0.00, value=0.00, step=0.01)

            submitted = st.form_submit_button("💾 Zatwierdź przyjęcie", type="primary")
            
            if submitted:
                if nazwa_input:
                    nowy_towar = {"nazwa": nazwa_input, "liczba": liczba_input, "cena": cena_input}
                    try:
                        supabase.table('produkty').insert(nowy_towar).execute()
                        dodaj_log(nazwa_input, "PRZYJĘCIE", liczba_input)
                        st.success("✅ Dodano!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd bazy danych: {e}")
                else:
                    st.warning("⚠️ Podaj nazwę produktu.")

    # --- DASHBOARD ---
    try:
        df = pobierz_magazyn()
        
        if not df.empty:
            # === KLUCZOWA POPRAWKA (FIX DLA BŁĘDU JSON/NaN) ===
            # Konwertujemy na liczby, a błędy/puste zamieniamy na 0
            df.columns = [c.lower() for c in df.columns]
            
            if 'liczba' in df.columns:
                df['liczba'] = pd.to_numeric(df['liczba'], errors='coerce').fillna(0)
            else:
                df['liczba'] = 0

            if 'cena' in df.columns:
                df['cena'] = pd.to_numeric(df['cena'], errors='coerce').fillna(0.0)
            else:
                df['cena'] = 0.0

            # Obliczenia metryk
            total_items = len(df)
            total_stock = int(df['liczba'].sum())
            total_value = (df['liczba'] * df['cena']).sum()

            m1, m2, m3 = st.columns(3)
            m1.metric("📦 SKU", f"{total_items}")
            m2.metric("📊 Stan", f"{total_stock:,}".replace(",", " "))
            m3.metric("💰 Wartość", f"{total_value:,.2f} PLN".replace(",", " "))
            
            st.write("")

            tab1, tab2 = st.tabs(["📋 Stan Magazynowy", "📜 Historia"])

            with tab1:
                # Bezpieczne obliczanie maksimum dla paska postępu
                max_val = df['liczba'].max()
                # Jeśli max to 0 lub NaN, ustawiamy domyślnie 100, żeby pasek się nie zepsuł
                safe_max = int(max_val * 1.2) if (not pd.isna(max_val) and max_val > 0) else 100

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_order=['id', 'nazwa', 'liczba', 'cena'],
                    column_config={
                        "id": st.column_config.TextColumn("ID", width="small"),
                        "nazwa": st.column_config.TextColumn("Produkt", width="large"),
                        "liczba": st.column_config.ProgressColumn(
                            "Stan",
                            format="%d szt.",
                            min_value=0,
                            max_value=safe_max
                        ),
                        "cena": st.column_config.NumberColumn("Cena", format="%.2f zł")
                    }
                )

                # Usuwanie
                with st.expander("🗑️ Usuwanie"):
                    if 'id' in df.columns:
                        c_d1, c_d2 = st.columns([3,1])
                        with c_d1:
                            opcje = df.apply(lambda x: f"ID {x['id']}: {x['nazwa']}", axis=1)
                            to_del = st.selectbox("Wybierz", opcje, label_visibility="collapsed")
                        with c_d2:
                            if st.button("Usuń", type="primary"):
                                id_del = int(to_del.split("ID ")[1].split(":")[0])
                                name_del = to_del.split(":")[1].strip()
                                supabase.table('produkty').delete().eq('id', id_del).execute()
                                dodaj_log(name_del, "USUNIĘCIE", 0)
                                st.rerun()

            with tab2:
                # Pobieranie historii - bezpiecznie
                try:
                    res = supabase.table('historia').select("*").order("id", desc=True).limit(50).execute()
                    df_hist = pd.DataFrame(res.data)
                    if not df_hist.empty:
                        st.dataframe(df_hist, use_container_width=True, hide_index=True)
                    else:
                        st.info("Brak historii.")
                except:
                    st.warning("Tabela 'historia' nie istnieje w bazie danych. Wykonaj SQL z instrukcji.")

        else:
            st.info("Magazyn pusty.")

    except Exception as e:
        st.error("Wystąpił nieoczekiwany błąd.")
        st.write(e)

if __name__ == "__main__":
    main()
