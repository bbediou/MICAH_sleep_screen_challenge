import streamlit as st
import pandas as pd
import ssl
import certifi
import urllib3
import altair as alt
import requests
import io

# This line bypasses SSL verification.
ssl._create_default_https_context = ssl._create_unverified_context

# Configuration de la page (DOIT être la première commande st)
st.set_page_config(
    page_title="Ton Bilan",
    page_icon="🌙",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Configuration - CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRCbQDPet7-hUdVO0-CzfC3KrhHY6JbUO4UlMpUwbJJ_cp2LhqJSnX34jD-xqZcFAmI4FZZcEg9Wsuj/pub?output=csv"


# Charger les données et afficher les noms des colonnes
@st.cache_data
def load_data():
    df = pd.read_csv(SHEET_URL)
    return df


# Charger les données
df = load_data()

# Afficher les noms des colonnes
st.write("Noms des colonnes :")
st.write(list(df.columns))

# Ou afficher plus d'informations sur la structure des données
st.write("Informations sur les données :")
st.write(f"Nombre de lignes : {len(df)}")
st.write(f"Nombre de colonnes : {len(df.columns)}")
st.write("Colonnes :", df.columns.tolist())

# Afficher un aperçu des données
st.write("Aperçu des données :")
st.dataframe(df.head())

# Section pour le code secret
st.subheader("🔒 Validation du code secret")
secret_code = st.text_input("Entre ton code secret :")

# Variables pour stocker les données du participant
participant_data = None
valid_code = False

if secret_code:
    if secret_code in df["Choisis ton code secret"].values:
        st.success("Code secret valide! Tu peux voir tes résultats.")
        participant_data = df[df["Choisis ton code secret"] == secret_code].iloc[0]
        valid_code = True
    else:
        st.error("Code secret invalide. Vérifie ton code et réessaie.")

# Graphique en barres pour la colonne sommeil
st.subheader("🌙 Qualité du sommeil réparateur")

sleep_column = "A quel point ton sommeil est-il réparateur ?"
category_column = "Tu es :"

if sleep_column in df.columns and category_column in df.columns:
    # Créer un tableau croisé dynamique pour compter les combinaisons
    crosstab = pd.crosstab(df[sleep_column], df[category_column])

    # Convertir en format long pour Altair
    chart_data = crosstab.reset_index().melt(
        id_vars=[sleep_column],
        var_name='Catégorie',
        value_name='Nombre'
    )
    chart_data = chart_data.rename(columns={sleep_column: 'Sommeil'})

    # Créer le graphique groupé avec Altair
    bars = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Sommeil:O', title='Niveau de sommeil réparateur'),
        y=alt.Y('Nombre:Q', title='Nombre de réponses'),
        color=alt.Color('Catégorie:N',
                        title='Catégorie',
                        scale=alt.Scale(scheme='category10')),
        xOffset='Catégorie:N',  # Ceci place les barres côte à côte
        tooltip=['Sommeil', 'Catégorie', 'Nombre']
    )

    # Si un code valide est entré, ajouter le marquage du participant
    if valid_code and participant_data is not None:
        participant_sleep = participant_data[sleep_column]
        participant_category = participant_data[category_column]

        # Afficher les informations du participant
        st.info(f"🎯 **Ton score :** {participant_sleep}")

        # Calculer la hauteur maximale pour positionner le marqueur
        max_height = chart_data['Nombre'].max()

        # Créer les données pour le marqueur - point unique
        marker_data = pd.DataFrame({
            'Sommeil': [participant_sleep],
            'y_pos': [-1]  # Position au-dessus des barres
        })

        # Créer le marqueur (étoile rouge) - sans groupement par catégorie
        marker = alt.Chart(marker_data).mark_point(
            shape='arrow',
            size=500,
            color='red',
            strokeWidth=3,
        ).encode(
            x=alt.X('Sommeil:O'),
            y=alt.Y('y_pos:Q'),
            tooltip=alt.value(f'Votre réponse: {participant_sleep}')
        )

        #Define rectangle coordinates
        # Get max height for the chart
        max_height = chart_data['Nombre'].max()

        # --- Create rectangle highlight around the participant's x position ---
        # Determine which x-position to highlight (ordinal position)
        rect_data = pd.DataFrame([{
            "Sommeil": participant_sleep,
            "y_start": 0,
            "y_end": max_height
        }])

        rect = (
            alt.Chart(rect_data)
            .mark_rect(
                fill="lightgrey",  # subtle highlight
                opacity=0.3,
                stroke="red",
                strokeWidth=1
            )
            .encode(
                x=alt.X("Sommeil:O"),  # same encoding type as bar chart
                x2="Sommeil",  # same category; Altair will center it
                y=alt.Y("y_start:Q"),
                y2="y_end:Q"
            )
        )


        # Combiner tous les éléments
        chart = alt.layer(
            bars,
            marker,
            rect
        ).resolve_scale(
            color='independent'
        ).properties(
            width=600,
            height=400,
            title='Distribution des réponses sur la qualité du sommeil par catégorie (⭐ = votre réponse)'
        )

    else:
        chart = bars.properties(
            width=600,
            height=400,
            title='Distribution des réponses sur la qualité du sommeil par catégorie'
        )

    st.altair_chart(chart, use_container_width=True)

else:
    missing_cols = []
    if sleep_column not in df.columns:
        missing_cols.append(sleep_column)
    if category_column not in df.columns:
        missing_cols.append(category_column)

    st.error(f"Colonnes manquantes : {missing_cols}")
    st.write("Colonnes disponibles :")
    st.write(df.columns.tolist())