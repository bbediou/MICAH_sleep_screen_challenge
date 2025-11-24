import streamlit as st
import pandas as pd
import ssl
import certifi
import urllib3
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


# Fonction pour créer des données fictives
@st.cache_data
def create_fake_data():
    """Créer des données fictives pour tester le graphique en donut"""
    np.random.seed(42)  # Pour des résultats reproductibles

    # Définir les options possibles
    screen_times = ["0-1 heure", "1-2 heures", "2-3 heures", "3-4 heures", "Plus de 4 heures"]
    categories = ["Adolescent", "Adulte"]
    codes = [f"CODE{i:03d}" for i in range(1, 51)]  # 50 codes secrets

    # Générer des données fictives
    data = []
    for i in range(50):  # 50 participants fictifs
        data.append({
            "Choisis ton code secret": codes[i],
            "Combien d'heures passes-tu sur les écrans le soir ?": np.random.choice(screen_times),
            "Tu es :": np.random.choice(categories)
        })

    return pd.DataFrame(data)


# Configuration - utiliser les données fictives au lieu du Google Sheet
USE_FAKE_DATA = st.sidebar.checkbox("Utiliser des données fictives pour les tests", value=True)


# Charger les données
@st.cache_data
def load_data():
    if USE_FAKE_DATA:
        return create_fake_data()
    else:
        SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRCbQDPet7-hUdVO0-CzfC3KrhHY6JbUO4UlMpUwbJJ_cp2LhqJSnX34jD-xqZcFAmI4FZZcEg9Wsuj/pub?output=csv"
        df = pd.read_csv(SHEET_URL)
        return df


df = load_data()

# Afficher le mode actuel
if USE_FAKE_DATA:
    st.info("🧪 **Mode test activé** - Utilisation de données fictives")
    st.write("💡 Codes de test disponibles : CODE001, CODE002, CODE003... CODE050")

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

# Nouveau graphique en donut - Temps d'écran le soir par catégorie
st.subheader("📱 Temps d'écran le soir par catégorie")

screen_time_column = "Combien d'heures passes-tu sur les écrans le soir ?"
category_column = "Tu es :"
screen_times = ["0-1 heure", "1-2 heures", "2-3 heures", "3-4 heures", "Plus de 4 heures"]

if screen_time_column in df.columns and category_column in df.columns:
    # Créer un tableau croisé dynamique
    crosstab = pd.crosstab(df[screen_time_column], df[category_column])

    # Préparer les données pour le donut
    screen_time_counts = df[screen_time_column].value_counts().reindex(screen_times, fill_value=0)


    # Afficher les statistiques
    st.write("**Répartition du temps d'écran :**")
    for time_range, count in screen_time_counts.items():
        percentage = (count / len(df)) * 100
        st.write(f"- **{time_range}** : {count} personnes ({percentage:.1f}%)")

    # Si un code valide est entré, afficher les informations du participant
    if valid_code and participant_data is not None:
        participant_screen_time = participant_data[screen_time_column]
        participant_category = participant_data[category_column]

        st.info(f"🎯 **Ton temps d'écran le soir :** {participant_screen_time}")
        st.info(f"👤 **Tu es :** {participant_category}")


    # Créer le graphique en donut avec matplotlib et seaborn
    fig, ax = plt.subplots(figsize=(10, 8))

    # Réordonner selon l'ordre souhaité au lieu de l'ordre des fréquences
    # screen_time_counts_ordered = pd.Series(dtype='int64')
    # for time_range in screen_times:
    #     if time_range in df[screen_time_column].values:
    #         count = df[screen_time_column].value_counts()[time_range]
    #         screen_time_counts_ordered[time_range] = count
    #     else:
    #         screen_time_counts_ordered[time_range] = 0

    # Définir les couleurs avec une palette seaborn
    #colors = sns.color_palette("Set3", len(screen_time_counts))

    # Créer la liste des couleurs dans l'ordre des données
    colors_manual = {
        "0-1 heure": "#A8E6A3",  # Vert pastel (le plus faible)
        "1-2 heures": "#B8E0D2",  # Vert-bleu pastel
        "2-3 heures": "#D4EDDA",  # Vert très clair
        "3-4 heures": "#FFE4B5",  # Beige-orange pastel
        "Plus de 4 heures": "#FFB347"  # Orange pastel (le plus élevé)
    }
    colors = [colors_manual[time_range] for time_range in screen_times]

    # Créer le graphique en donut
    wedges, texts, autotexts = ax.pie(
        screen_time_counts.values,
        labels=screen_time_counts.index,
        autopct='%1.1f%%',
        colors=colors,
        pctdistance=0.85,
        startangle=90
    )

    # Créer le trou au centre pour faire un donut
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    ax.add_artist(centre_circle)

    # Améliorer l'apparence
    plt.setp(autotexts, size=10, weight="bold")
    plt.setp(texts, size=9)

    ax.set_title("Répartition du temps d'écran le soir",
                 fontsize=14, fontweight='bold', pad=20)

    # Si un code valide est entré, mettre en évidence la réponse du participant
    if valid_code and participant_data is not None:
        participant_screen_time = participant_data[screen_time_column]
        participant_index = list(screen_time_counts.index).index(participant_screen_time)
        wedges[participant_index].set_edgecolor('red')
        wedges[participant_index].set_linewidth(3)

    # Afficher le graphique dans Streamlit
    st.pyplot(fig)


    # Graphique détaillé par catégorie avec Streamlit
    st.subheader("📊 Détail par catégorie")

    # Afficher un graphique en barres avec Streamlit
    st.bar_chart(crosstab)

    # Tableau de données détaillées
    st.subheader("📋 Données détaillées")

    # Calculer les pourcentages
    crosstab_percent = pd.crosstab(df[screen_time_column], df[category_column], normalize='index') * 100

    # Afficher le tableau croisé avec les pourcentages
    st.write("**Pourcentages par ligne (temps d'écran) :**")
    st.dataframe(crosstab_percent.round(1))

    # Afficher aussi les nombres absolus
    st.write("**Nombres absolus :**")
    st.dataframe(crosstab)

else:
    missing_cols = []
    if screen_time_column not in df.columns:
        missing_cols.append(screen_time_column)
    if category_column not in df.columns:
        missing_cols.append(category_column)

    st.error(f"Colonnes manquantes : {missing_cols}")
    st.write("Colonnes disponibles :")
    st.write(df.columns.tolist())