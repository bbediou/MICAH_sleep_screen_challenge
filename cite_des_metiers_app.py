import streamlit as st
import pandas as pd
import ssl
import certifi
import urllib3
import altair as alt
import requests
import io
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np



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
    # Convertir la colonne Timestamp en datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%m/%d/%Y %H:%M:%S')

    # Définir la date de référence (18 novembre 2025)
    reference_date = pd.to_datetime('11/18/2025', format='%m/%d/%Y')

    # Filtrer les données pour ne garder que celles après le 18/11/2025
    df_filtered = df[df['Timestamp'] > reference_date]

    return df_filtered


# Charger les données
df = load_data()

# Ou afficher plus d'informations sur la structure des données
st.write("Informations sur les données :")
st.write(f"Nombre de lignes : {len(df)}")
st.write(f"Nombre de colonnes : {len(df.columns)}")
st.write("Colonnes :", df.columns.tolist())

# Afficher un aperçu des données
st.write("Aperçu des données :")
st.dataframe(df.head())


### Functions
# Fonction pour créer un graphique Likert
def create_likert_chart(data, question_col, title, participant_answer=None):
    """
    Crée un graphique Likert horizontal
    """
    # Compter les réponses
    counts = data[question_col].value_counts()

    # Calculer les pourcentages
    percentages = (counts / len(data)) * 100

    # Créer le graphique
    fig, ax = plt.subplots(figsize=(12, 6))

    # Définir les couleurs pour l'échelle Likert (du négatif au positif)
    colors = ['#d32f2f', '#f57c00', '#fbc02d', '#388e3c']  # Rouge, Orange, Jaune, Vert

    # Créer les barres horizontales
    bars = ax.barh(range(len(counts)), percentages.values,
                   color=colors[:len(counts)], alpha=0.7, edgecolor='black', linewidth=1)

    # Mettre en évidence la réponse du participant si elle existe
    if participant_answer is not None and participant_answer in counts.index:
        participant_idx = list(counts.index).index(participant_answer)
        bars[participant_idx].set_edgecolor('red')
        bars[participant_idx].set_linewidth(3)
        bars[participant_idx].set_alpha(1.0)

    # Personnaliser le graphique
    ax.set_yticks(range(len(counts)))
    ax.set_yticklabels(counts.index, fontsize=11)
    ax.set_xlabel('Pourcentage des réponses (%)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # Ajouter les valeurs sur les barres
    for i, (bar, count, pct) in enumerate(zip(bars, counts.values, percentages.values)):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f'{count} ({pct:.1f}%)',
                ha='left', va='center', fontweight='bold', fontsize=10)

    # Améliorer l'apparence
    ax.set_xlim(0, max(percentages.values) * 1.2)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    return fig


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

# Nouveau graphique Likert pour les écrans avant de dormir
st.subheader("📱 Habitudes d'écrans avant le sommeil")

screen_habit_column = 'As-tu l’habitude de regarder des écrans avant de dormir?'

if screen_habit_column in df.columns:
    # Afficher les statistiques
    screen_counts = df[screen_habit_column].value_counts()

    st.write("**Répartition des réponses :**")
    for answer, count in screen_counts.items():
        percentage = (count / len(df)) * 100
        st.write(f"- **{answer}** : {count} personnes ({percentage:.1f}%)")

    # Si un code valide est entré, afficher la réponse du participant
    participant_screen_habit = None
    if valid_code and participant_data is not None:
        participant_screen_habit = participant_data[screen_habit_column]
        st.info(f"🎯 **Ta réponse :** {participant_screen_habit}")

    # Créer et afficher le graphique Likert
    fig = create_likert_chart(
        df,
        screen_habit_column,
        "Habitudes d'écrans avant le sommeil - Échelle de Likert",
        participant_screen_habit
    )

    st.pyplot(fig)

    # Ajouter une légende si un participant est mis en évidence
    if valid_code and participant_data is not None:
        st.caption("🔴 **Barre avec bordure rouge** : Votre réponse")

else:
    st.error(f"Colonne '{screen_habit_column}' non trouvée dans les données")
    st.write("Colonnes disponibles :")
    st.write(df.columns.tolist())
