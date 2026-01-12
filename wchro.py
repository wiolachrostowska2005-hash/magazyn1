import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- KONFIGURACJA SUPABASE ---
# Pobieramy dane z sekretów (st.secrets)
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
except FileNotFoundError:
    st.error("Brak pliku secrets.toml lub konfiguracji w Streamlit Cloud!")
    st.stop()

# Tworzenie klienta połączenia
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- INTERFEJS STREAMLIT ---
st.title("☁️ System Magazynowy (Supabase Cloud)")

tab1, tab2, tab3 = st.tabs(["Dodaj Kategorię", "Dodaj Produkt", "Podgląd Bazy"])

# --- ZAKŁADKA 1: DODAWANIE KATEGORII ---
with tab1:
    st.header("Nowa Kategoria")
    with st.form("form_kategoria"):
        kat_nazwa = st.text_input("Nazwa kategorii")
        kat_opis = st.text_area("Opis kategorii")
        submitted_kat = st.form_submit_button("Dodaj kategorię")
        
        if submitted_kat and kat_nazwa:
            try:
                # Wstawianie danych do Supabase
                data = {"nazwa": kat_nazwa, "opis": kat_opis}
                supabase.table("kategoria").insert(data).execute()
                st.success(f"Dodano kategorię: {kat_nazwa}")
            except Exception as e:
                st.error(f"Błąd zapisu: {e}")

# --- ZAKŁADKA 2: DODAWANIE PRODUKTU ---
with tab2:
    st.header("Nowy Produkt")
    
    # 1. Pobieramy listę kategorii z Supabase
    response = supabase.table("kategoria").select("id, nazwa").execute()
    kategorie_data = response.data
    
    if not kategorie_data:
        st.warning("Najpierw dodaj kategorię w pierwszej zakładce!")
    else:
        # Tworzymy słownik {Nazwa: ID}
        opcje_kategorii = {item['nazwa']: item['id'] for item in kategorie_data}
        
        with st.form("form_produkt"):
            prod_nazwa = st.text_input("Nazwa produktu")
            prod_liczba = st.number_input("Ilość", min_value=1, step=1)
            prod_cena = st.number_input("Cena (PLN)", min_value=0.01, step=0.01, format="%.2f")
            wybrana_kat_nazwa = st.selectbox("Wybierz kategorię", options=list(opcje_kategorii.keys()))
            
            submitted_prod = st.form_submit_button("Dodaj produkt")
            
            if submitted_prod and prod_nazwa:
                wybrane_id = opcje_kategorii[wybrana_kat_nazwa]
                
                # Przygotowanie danych (zwróć uwagę na nazwy kolumn z Twojego zdjęcia!)
                # Użyłem 'Kategoria_id' zgodnie z Twoim zdjęciem, ale upewnij się co do wielkości liter w Supabase
                nowy_produkt = {
                    "nazwa": prod_nazwa,
                    "liczba": prod_liczba,
                    "cena": prod_cena,
                    "Kategoria_id": wybrane_id 
                }
                
                try:
                    supabase.table("produkty").insert(nowy_produkt).execute()
                    st.success(f"Dodano produkt: {prod_nazwa}")
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")

# --- ZAKŁADKA 3: PODGLĄD DANYCH ---
with tab3:
    st.header("Stan Magazynu")
    
    # Pobieranie danych z łączeniem tabel (Joins w Supabase są super proste!)
    # Składnia: '*, kategoria(nazwa)' oznacza: pobierz wszystko z produktów i nazwę z połączonej tabeli kategoria
    try:
        response = supabase.table("produkty").select("*, kategoria(nazwa)").execute()
        dane = response.data
        
        if dane:
            # Dane przychodzą jako lista słowników, trzeba je "spłaszczyć" dla Pandas
            # Bo kategoria przyjdzie jako {'nazwa': 'Elektronika'} wewnątrz produktu
            clean_data = []
            for row in dane:
                item = {
                    "ID": row['id'],
                    "Produkt": row['nazwa'],
                    "Ilość": row['liczba'],
                    "Cena": f"{row['cena']:.2f} zł",
                    # Obsługa sytuacji, gdyby kategoria została usunięta
                    "Kategoria": row['kategoria']['nazwa'] if row['kategoria'] else "Brak"
                }
                clean_data.append(item)

            df = pd.DataFrame(clean_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Baza jest pusta.")
            
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
