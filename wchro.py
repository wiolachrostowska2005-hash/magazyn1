import streamlit as st

# Konfiguracja strony (tytuł i ikona w przeglądarce)
st.set_page_config(page_title="Prosty Magazyn", page_icon="📦")

# --- INICJALIZACJA STANU (PAMIĘCI TYMCZASOWEJ) ---
# Sprawdzamy, czy w sesji istnieje już lista towarów. Jeśli nie, tworzymy ją.
if 'magazyn' not in st.session_state:
    st.session_state.magazyn = ["Przykładowy towar A", "Przykładowy towar B"]

# --- TYTUŁ APLIKACJI ---
st.title("📦 Prosty Magazyn (Streamlit)")
st.markdown("Aplikacja działa w pamięci RAM. Odświeżenie strony może zresetować listę.")

# --- PANEL BOCZNY: DODAWANIE TOWARU ---
with st.sidebar:
    st.header("Dodaj nowy towar")
    nowy_towar = st.text_input("Nazwa produktu", key="input_towar")
    
    if st.button("Dodaj do magazynu"):
        if nowy_towar:
            # Dodanie do listy w session_state
            st.session_state.magazyn.append(nowy_towar)
            st.success(f"Dodano: {nowy_towar}")
        else:
            st.warning("Wpisz nazwę towaru!")

# --- GŁÓWNY WIDOK: LISTA TOWARÓW ---
st.header("Aktualny stan magazynowy")

if len(st.session_state.magazyn) > 0:
    # Wyświetlanie listy
    for index, towar in enumerate(st.session_state.magazyn):
        st.text(f"{index + 1}. {towar}")
else:
    st.info("Magazyn jest pusty.")

st.divider()

# --- USUWANIE TOWARU ---
st.subheader("Usuń towar")

if len(st.session_state.magazyn) > 0:
    # Wybieramy towar z listy rozwijanej (selectbox)
    towar_do_usuniecia = st.selectbox(
        "Wybierz towar do usunięcia:", 
        options=st.session_state.magazyn
    )
    
    if st.button("Usuń wybrany towar"):
        if towar_do_usuniecia in st.session_state.magazyn:
            st.session_state.magazyn.remove(towar_do_usuniecia)
            st.success("Usunięto towar!")
            st.rerun() # Przeładowanie aplikacji, aby odświeżyć listę natychmiast
else:
    st.write("Brak towarów do usunięcia.")
