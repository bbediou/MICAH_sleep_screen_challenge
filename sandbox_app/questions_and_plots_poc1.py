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
    page_title="Question et Bilan",
    page_icon="🌙",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🧠 Questionnaire sur ton sommeil")

st.markdown("**Réponds à ces questions puis valide tes réponses.**")

# --- Formulaire de saisie ---
with st.form("survey_form"):
    # Question 1
    category = st.radio(
        "Tu es :",
        ["🧑‍🎓 Je suis un·e ado", "🧑‍💼 Je suis parent", "👩‍🏫 Je suis enseignant·e"]
    )

    # Question 2
    sleep_score = st.slider(
        "À quel point ton sommeil est-il réparateur ?",
        min_value=1,
        max_value=5,
        value=3,
        help="1 = pas du tout réparateur, 5 = très réparateur"
    )

    # Question 3
    secret_code_input = st.text_input(
        "Choisis ton code secret",
        help="Facile à retenir, il servira pour voir tes résultats"
    )

    submitted = st.form_submit_button("📤 Envoyer mes réponses")

if submitted:
    if not secret_code_input.strip():
        st.error("Merci de saisir un code secret avant d’envoyer.")
    else:
        # Envoi des données vers la feuille Google
        form_url = "https://docs.google.com/forms/d/e/1FAIpQLSfiY2oRtI1BEM3fHaB2qe6Y_HzyzdaYUgDO6qk3K_whTGxHqw/viewform"

        form_data = {
            "entry.242282797": category,        # Remplace par les entry IDs
            "entry.452218019": sleep_score,
            "entry.771045250": secret_code_input
        }

        response = requests.post(form_url, data=form_data)
        if response.status_code == 200:
            st.success("✅ Tes réponses ont bien été enregistrées !")
        else:
            st.warning("⚠️ Une erreur est survenue. Essaie à nouveau plus tard.")

#--- Well-play ad to share on whatsapp ---
st.markdown("""
## 🌿 Étude scientifique **Well-Play**

L’étude  **Well-Play** est un projet de recherche scientifique de l'**UNIGE** et la **HedS**.

🔍 Objectif : Comprendre le lien entre jeu, bien-être et apprentissage chez les adolescent-es de 11 à 15 ans (inclus).

🗓️ Déroulement : Après un 1er rendez-vous à l’université, depuis chez eux, les adolescent.e.s sont peut-être [invité.es](http://xn--invit-fsa.es/) à jouer pendant 6 semaines à un jeu fourni par l'équipe de recherche, dans un cadre modéré. Après 6 semaines, un 2e rendez-vous à l’université a lieu, puis un dernier rendez-vous 4 mois plus tard.

🎁 Un don de 40 CHF au nom du/de la participant.e est fait à l’association pour l’écologie de son choix et jusqu’à 60 CHF de bons cadeau Galaxus offerts au/à la participant.e.

✅ **Plus d’information et inscription** (à faire par un parent) **:**

🔗 [https://well-play-teen.org](https://well-play-teen.org)

Pour toute question, contactez : [**wellplay@unige.ch**](mailto:wellplay@unige.ch)
""", unsafe_allow_html=True)

# --- Message WhatsApp pré-rempli ---
whatsapp_message = (
    "J'ai trouvé une étude de recherche scientifique de l'UNIGE et la HedS appelée Well-Play.%0A%0A"
    "**Le but :** comprendre le lien entre jeu vidéo, le bien-être et les apprentissages des ados entre 11 et 15 ans (inclus).%0A%0A"
    "Participer à cette étude permet de soutenir la recherche mais aussi l’écologie puisqu’un don de 40 CHF en mon nom sera fait à l’association de mon choix "
    "et jusqu’à 60 CHF de bons cadeau Galaxus me seront offerts en dédommagement.%0A%0A"
    "**J’aimerais beaucoup y participer !**%0A%0A"
    "Pour ça, l'équipe de recherche a besoin de l’autorisation d’un parent (son consentement).%0A%0A"
    "C'est vous qui devez lire tous les détails et m'inscrire.%0A%0A"
    "**S'il vous plaît, cliquez sur le lien ci-dessous pour voir si je peux y participer :**%0A%0A"
    "https://well-play-teen.org%0A%0A"
    "Pour toute question, contactez : wellplay@unige.ch%0A%0A"
    "Partagez ce message à vos contacts qui pourraient être intéressés également."
)

whatsapp_link = f"https://wa.me/?text={whatsapp_message}"

# --- Bouton WhatsApp centré avec icône ---
st.markdown(f"""
<div style="text-align:center;">
<a href="{whatsapp_link}" target="_blank" style="
        display:inline-flex;
        align-items:center;
        justify-content:center;
        background-color:#25D366;
        color:white;
        padding:12px 24px;
        border-radius:12px;
        text-decoration:none;
        font-weight:600;
        font-size:17px;
        box-shadow:0 2px 6px rgba(0,0,0,0.2);
        transition:all 0.2s ease-in-out;">
<img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg"
             alt="WhatsApp" width="24" height="24" style="margin-right:10px;">
        Partager sur WhatsApp
</a>
</div>
""", unsafe_allow_html=True)


### See plot


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