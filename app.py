import streamlit as st
import pandas as pd
import random
import calendar
import plotly.express as px
from datetime import datetime, timedelta

# Ustawienia konfiguracji strony
st.set_page_config(
    layout="wide",
    page_title="Interaktywna Baza Polskiego Rapu",
    page_icon="🎤",
    initial_sidebar_state="expanded"
)

# Funkcja wczytująca dane z pliku CSV
@st.cache_data
def load_data():
    try:
        # Optymalizacja pamięci przez określenie typów kolumn
        data = pd.read_csv(
            "polskirap2.csv", 
            sep=",",
            dtype={
                'artist': 'string',
                'album_title': 'string',
                'year': 'string',  # Tymczasowo jako string dla walidacji
                'label': 'string',
                'track_count': 'Int32',
                'tracklist': 'string',
                'thumb': 'string'
            }
        )
        # Konwersja roku na int, usuwając błędne wartości
        data['year'] = data['year'].apply(
            lambda x: int(x.replace(',', '')) if pd.notna(x) and x.replace(',', '').isdigit() else None
        )
        st.info(f"Wczytano {len(data)} rekordów z pliku CSV.")
        return data
    except Exception as e:
        st.error(f"Błąd podczas wczytywania danych: {e}")
        return pd.DataFrame()

# Funkcja generująca losowy zestaw płyt do odkrywania
@st.cache_data
def generate_discover_list(data, start_year, end_year, label_filter):
    # Filtrowanie danych na podstawie podanych kryteriów
    filtered_data = data[
        (data['year'].between(start_year, end_year)) &
        (~data['artist'].str.contains("Various", na=False)) &
        (~data['label'].str.contains("Dee Jay Mix Club|Nielegal", na=False))
    ]
    if label_filter:
        filtered_data = filtered_data[filtered_data['label'].str.contains(label_filter, na=False)]
    
    # Sortowanie danych po roku wydania i losowanie 30 unikalnych albumów
    discover_data = filtered_data.sample(n=min(30, len(filtered_data)), random_state=42)
    return discover_data.reset_index(drop=True)

# Funkcja tworząca interaktywny kalendarz z miniaturami
def create_interactive_calendar(discover_data):
    today = datetime.now()
    st.markdown(f"## 🗓️ Odkryj Rap - {today.strftime('%B %Y')}")
    st.markdown(
        "### 🕵️ 30 płyt na 30 dni: "
        "Codziennie odkryj nowy album z polskiego rapu. Zobacz, co kryje się w Twoim kalendarzu!"
    )

    # Generowanie dni od aktualnego dnia na 30 dni do przodu
    dates = [today + timedelta(days=i) for i in range(30)]

    # Tworzenie widoku w układzie tygodniowym
    week_data = [dates[i:i + 7] for i in range(0, len(dates), 7)]
    
    for week in week_data:
        cols = st.columns(len(week))
        for idx, date in enumerate(week):
            with cols[idx]:
                st.markdown(f"**{date.day} {date.strftime('%b')}**")
                if len(discover_data) > idx:
                    album = discover_data.iloc[idx]
                    st.image(album['thumb'], width=100) if pd.notna(album['thumb']) else st.text("Brak zdjęcia")
                    st.markdown(f"🎵 **{album['artist']} - {album['album_title']} ({album['year']})**")
                else:
                    st.text("Brak albumu")

# Wczytanie danych
with st.spinner("Wczytywanie danych..."):
    data = load_data()

# Tytuł aplikacji
st.title("🎤 Interaktywna Baza Polskiego Rapu")
st.markdown("""Aplikacja umożliwia przeglądanie, filtrowanie i odkrywanie informacji o polskich albumach rapowych.""")

# Zakładki
tabs = st.tabs(["🎤 Filtry i wyniki", "📊 Statystyki", "📈 Wizualizacje", "🎲 Odkryj Rap"])

# Zakładka 1: Filtry i wyniki
with tabs[0]:
    st.subheader("🎤 Wyszukiwanie albumów")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        artist_filter = st.text_input("Wykonawca:", key="filters_artist")
    with col2:
        year_filter = st.slider("Zakres lat wydania:", 1991, 2024, (1991, 2024), key="filters_year")
    with col3:
        label_filter = st.text_input("Wytwórnia:", key="filters_label")
    with col4:
        track_filter = st.text_input("Szukaj w tracklistach:", key="filters_tracklist")

    filtered_data = data[
        (data['artist'].str.contains(artist_filter, na=False)) &
        (data['year'].between(year_filter[0], year_filter[1])) &
        (data['label'].str.contains(label_filter, na=False)) &
        (data['tracklist'].str.contains(track_filter, na=False)) &
        (~data['artist'].str.contains("Various", na=False)) &
        (~data['label'].str.contains("Dee Jay Mix Club|Nielegal", na=False))
    ]

    st.write(f"Znaleziono {len(filtered_data)} wyników")
    st.write(f"Liczba wszystkich rekordów: {len(data)}")
    st.write(f"Liczba wyników po zastosowaniu filtrów: {len(filtered_data)}")

    results_per_page = 20
    total_pages = -(-len(filtered_data) // results_per_page)
    page = st.slider("Strona:", 1, total_pages, 1, key="filters_page")
    start_idx = (page - 1) * results_per_page
    end_idx = start_idx + results_per_page

    st.dataframe(filtered_data.iloc[start_idx:end_idx][['artist', 'album_title', 'year', 'label', 'track_count']])

# Zakładka 2: Statystyki
with tabs[1]:
    st.subheader("📊 Statystyki bazy")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Liczba albumów w dekadach")
        data['decade'] = (data['year'] // 10) * 10
        decade_counts = data['decade'].value_counts().sort_index()
        fig_decade = px.bar(
            x=decade_counts.index,
            y=decade_counts.values,
            labels={'x': 'Dekada', 'y': 'Liczba albumów'},
            title="Liczba albumów w poszczególnych dekadach"
        )
        st.plotly_chart(fig_decade, use_container_width=True)

    with col2:
        st.markdown("### Najbardziej aktywni artyści")
        artist_counts = data['artist'].value_counts().head(10)
        fig_artist = px.bar(
            x=artist_counts.index,
            y=artist_counts.values,
            labels={'x': 'Artysta', 'y': 'Liczba albumów'},
            title="Top 10 najbardziej aktywnych artystów"
        )
        st.plotly_chart(fig_artist, use_container_width=True)

    st.markdown("### Średnia liczba utworów w albumach dla wybranych lat")
    avg_tracks_per_year = data.groupby('year')['track_count'].mean().reset_index()
    fig_avg_tracks = px.line(
        avg_tracks_per_year, 
        x='year', 
        y='track_count', 
        labels={'year': 'Rok', 'track_count': 'Średnia liczba utworów'},
        title="Średnia liczba utworów w albumach na przestrzeni lat"
    )
    st.plotly_chart(fig_avg_tracks, use_container_width=True)

    st.markdown("### Liczba albumów na wykonawcę w wybranych dekadach")
    decade_artist_counts = data.groupby(['decade', 'artist']).size().reset_index(name='count')
    fig_decade_artist = px.bar(
        decade_artist_counts, 
        x='decade', 
        y='count', 
        color='artist', 
        labels={'decade': 'Dekada', 'count': 'Liczba albumów', 'artist': 'Artysta'},
        title="Liczba albumów na wykonawcę w poszczególnych dekadach"
    )
    st.plotly_chart(fig_decade_artist, use_container_width=True)

    st.markdown("### Filtry dla statystyk")
    filter_year_range = st.slider("Zakres lat do analizy:", int(data['year'].min()), int(data['year'].max()), (1990, 2024), key="stats_year_range")
    filtered_stats = data[
        (data['year'].between(filter_year_range[0], filter_year_range[1])) &
        (~data['artist'].str.contains("Various", na=False)) &
        (~data['label'].str.contains("Dee Jay Mix Club|Nielegal", na=False))
    ]

    st.write(f"Liczba albumów w wybranym zakresie lat: {len(filtered_stats)}")

    filtered_decade_counts = filtered_stats['decade'].value_counts().sort_index()
    fig_filtered_decade = px.bar(
        x=filtered_decade_counts.index,
        y=filtered_decade_counts.values,
        labels={'x': 'Dekada', 'y': 'Liczba albumów'},
        title="Liczba albumów w dekadach (filtr)"
    )
    st.plotly_chart(fig_filtered_decade, use_container_width=True)

# Zakładka 3: Wizualizacje
with tabs[2]:
    st.subheader("📈 Wizualizacje")

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_year = st.selectbox("Wybierz rok:", sorted(data['year'].unique()), key="visualizations_year_select")
    with col2:
        st.markdown(f"### Albumy wydane w roku {selected_year}")
        albums_in_year = data[data['year'] == selected_year]
        for row in albums_in_year.itertuples():
            st.markdown(f"- **{row.artist} - {row.album_title} ({row.year})**")

    st.markdown("### Popularność wytwórni w czasie")
    label_year_counts = data.groupby(['year', 'label']).size().reset_index(name='count')
    label_year_counts = label_year_counts[(~label_year_counts['label'].str.contains("Dee Jay Mix Club|Nielegal", na=False))]
    fig_labels = px.bar(
        label_year_counts,
        x='year',
        y='count',
        color='label',
        labels={'year': 'Rok', 'count': 'Liczba albumów', 'label': 'Wytwórnia'},
        title="Popularność wytwórni w czasie"
    )
    st.plotly_chart(fig_labels, use_container_width=True)

# Zakładka 4: Odkryj Rap
with tabs[3]:
    st.subheader("🎲 Odkryj Rap")

    # Ustawienia filtrów
    start_year, end_year = st.slider("Zakres lat:", 1991, 2024, (1991, 2024), key="discover_year_slider")
    label_filter = st.text_input("Wytwórnia (opcjonalnie):", key="discover_label_filter")

    # Generowanie listy albumów
    if st.button("Generuj listę", key="discover_generate_button"):
        discover_data = generate_discover_list(data, start_year, end_year, label_filter)
        if not discover_data.empty:
            create_interactive_calendar(discover_data)
        else:
            st.warning("Nie znaleziono albumów dla podanych kryteriów.")
