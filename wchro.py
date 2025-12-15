import streamlit as st

# 1. Konfiguracja strony - tytuł i ikonka
st.set_page_config(page_title="Mój Magazyn", page_icon="📝")

st.title("📝 Mój podręczny magazyn")
st.write("Wpisz towar poniżej i naciśnij Enter, aby go dodać! :3")

# 2. Tworzymy "pamięć" aplikacji (żeby towary nie znikały przy klikaniu)
if 'lista_towarow' not in st.session_state:
    st.session_state.lista_towarow = []

# --- SEKJA 1: DODAWANIE (To tutaj wpisujesz sama!) ---
with st.container():
    # Używamy st.form, żeby można było zatwierdzać Enterem
    with st.form(key='dodawanie_form'):
        nowy_produkt = st.text_input("📦 Wpisz nazwę produktu tutaj:")
        submit_button = st.form_submit_button(label='Dodaj produkt')

    # Co się dzieje po kliknięciu lub wciśnięciu Enter:
    if submit_button:
        if nowy_produkt:
            st.session_state.lista_towarow.append(nowy_produkt)
            st.success(f"Dodano: {nowy_produkt}")
        else:
            st.warning("Ej, nic nie wpisałaś! Wpisz nazwę towaru.")

st.divider() # Ozdobna linia oddzielająca

# --- SEKCJA 2: LISTA TOWARÓW (Wyświetlanie) ---
st.subheader("📋 Twoja lista:")

if st.session_state.lista_towarow:
    # Wyświetlamy każdy towar w ładnej ramce
    for i, towar in enumerate(st.session_state.lista_towarow):
        st.info(f"{i + 1}. {towar}")
else:
    st.write("Magazyn jest pusty... Dodaj coś u góry! ⬆️")

st.divider()

# --- SEKCJA 3: USUWANIE ---
st.subheader("🗑️ Usuwanie")

if st.session_state.lista_towarow:
    # Lista rozwijana do wyboru towaru do usunięcia
    do_usuniecia = st.selectbox(
        "Wybierz co chcesz wyrzucić:", 
        st.session_state.lista_towarow
    )
    
    if st.button("Usuń ten towar"):
        st.session_state.lista_towarow.remove(do_usuniecia)
        st.error(f"Usunięto: {do_usuniecia}")
        st.rerun() # Odświeżamy stronę natychmiast
