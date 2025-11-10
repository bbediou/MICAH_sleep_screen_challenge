import streamlit as st
import pandas as pd
import ssl
import certifi
import urllib3
import altair as alt
import requests  # <-- Add this
import io       # <-- Add this

# Mobile display configuration

# Create a session with custom SSL configuration
#http = urllib3.PoolManager(
#    cert_reqs='CERT_REQUIRED',
#    ca_certs=certifi.where()
#)

# This line bypasses SSL verification.
ssl._create_default_https_context = ssl._create_unverified_context

# Replace this URL with your Google Sheet's sharing URL
#SHEET_URL = st.text_input(
#    "Enter your Google Sheet URL",
#    "https://docs.google.com/spreadsheets/d/1Til8NWWAy1MVv5An3yUzXXEBSHocgzfe8SgkjcvKOmg/edit#gid=0"
#)
# Paste your "Publish to web" CSV link here
# (Go to File > Share > Publish to web > Get link as CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRCbQDPet7-hUdVO0-CzfC3KrhHY6JbUO4UlMpUwbJJ_cp2LhqJSnX34jD-xqZcFAmI4FZZcEg9Wsuj/pub?output=csv"

# The *exact* column name for your classifier (teen, parent, teacher)
CLASSIFIER_COL = "Tu es :"  # Example: "Are you a teen, parent, or teacher?"

# The *exact* column name for the user's unique identifier
IDENTIFIER_COL = "Choisis ton code secret" # Example: "Email Address" or "Your Secret Code"

# The *exact* column names for the questions you want to plot
# I've included one numerical and one categorical example
#NUMERICAL_QUESTION_COL = "A quel point ton sommeil est-il réparateur ?"
#CATEGORICAL_QUESTION_COL = "Combien d’heures passes-tu sur les écrans le soir ?"
SCALE_QUESTIONS = [
    "A quel point ton sommeil est-il réparateur ?",
    "Quelle est la qualité de ton sommeil ?"
]

# Mettez TOUTES vos questions à choix/catégoriques ici
CATEGORY_QUESTIONS = [
    "As tu des écrans dans ta chambre (smartphone compris) ?",
    "Scénario — “22 h 30",
    "Regardes-tu ton téléphone dès le réveil ?"
]
# --- (End of configuration) ---



# --- 2. CHARGEMENT DES DONNÉES ---
@st.cache_data(ttl=300)
def load_data(url):
    """Charge les données depuis le lien CSV publié."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        csv_data = io.StringIO(response.text)
        df = pd.read_csv(csv_data)
        return df
    except Exception as e:
        st.error(f"Erreur de chargement des données : {e}. Le lien SHEET_URL est-il correct et publié en CSV ?")
        return pd.DataFrame()

# --- 3. FONCTIONS DE PLOT (AMÉLIORÉES) ---

def plot_numerical_comparison(df, question_col, classifier_col, user_value):
    """
    Crée un histogramme (barres) coloré par groupe, avec une ligne rouge 
    pour la réponse de l'utilisateur.
    """
    # Ensure column names are safe for Vega-Lite/Altair by escaping colons
    # We create a plotting copy where any column name containing ':' is replaced
    # with an escaped version (backslash before colon) so Altair's "field:type"
    # parsing does not break.
    df_plot = df.copy()
    col_map = {col: (col.replace(':', '\\:') if isinstance(col, str) and ':' in col else col)
               for col in df_plot.columns}
    # Only rename if necessary
    if any(col_map[c] != c for c in col_map):
        df_plot = df_plot.rename(columns=col_map)

    q_field = col_map.get(question_col, question_col)
    cls_field = col_map.get(classifier_col, classifier_col)

    # Graphique de base : Histogramme de toutes les réponses
    base = alt.Chart(df_plot).mark_bar().encode(
        # Axe X : La question numérique
        x=alt.X(f"{q_field}:Q", bin=True, title=question_col),
        # Axe Y : Le nombre de réponses
        y=alt.Y('count()', title="Nombre de réponses"),
        # Couleur : Le type de répondant (ado, parent, etc.)
        color=alt.Color(f"{cls_field}:N", title="Type de répondant"),
        # Tooltip (info-bulle) au survol — use explicit Tooltip objects to keep
        # readable titles while referencing the escaped field names
        tooltip=[alt.Tooltip(q_field, type='quantitative', title=question_col),
                 alt.Tooltip(cls_field, type='nominal', title=classifier_col),
                 'count()']
    ).interactive()

    # Ligne rouge : une ligne verticale pour la réponse de l'utilisateur
    rule = alt.Chart(pd.DataFrame({'ma_reponse': [user_value]})).mark_rule(color='red', strokeWidth=3).encode(
        x='ma_reponse:Q',
        tooltip=alt.Tooltip('ma_reponse', title="Votre réponse")
    )
    
    return base + rule

def plot_categorical_comparison(df, question_col, classifier_col, user_value):
    """
    Crée un graphique à barres pour les catégories, en surlignant
    la réponse de l'utilisateur.
    """
    # Prepare a plotting copy with escaped column names (for colon-containing names)
    df_plot = df.copy()
    col_map = {col: (col.replace(':', '\\:') if isinstance(col, str) and ':' in col else col)
               for col in df_plot.columns}
    if any(col_map[c] != c for c in col_map):
        df_plot = df_plot.rename(columns=col_map)

    q_field = col_map.get(question_col, question_col)
    cls_field = col_map.get(classifier_col, classifier_col)

    # Créer une condition : 1.0 (opaque) si c'est la réponse de l'utilisateur, 0.3 (transparent) sinon
    opacity_condition = alt.condition(
        alt.datum[q_field] == user_value,
        alt.value(1.0),
        alt.value(0.3)
    )

    # Graphique principal : barres empilées
    chart = alt.Chart(df_plot).mark_bar().encode(
        # Axe X : La question catégorique
        x=alt.X(f"{q_field}:N", title=question_col),
        # Axe Y : Le nombre de réponses
        y=alt.Y('count()', title="Nombre de réponses"),
        # Couleur : Le type de répondant (crée les piles)
        color=alt.Color(f"{cls_field}:N", title="Type de répondant"),
        
        # Appliquer la condition d'opacité
        opacity=opacity_condition,
        
        # Tooltip — explicit fields
        tooltip=[alt.Tooltip(q_field, type='nominal', title=question_col),
                 alt.Tooltip(cls_field, type='nominal', title=classifier_col),
                 'count()']
    ).interactive()
    
    return chart

# --- 4. APPLICATION STREAMLIT ---

# Configuration de la page (DOIT être la première commande st)
st.set_page_config(
    page_title="Ton Bilan",
    page_icon="📊",
    layout="centered"  # Parfait pour les mobiles
)

st.title("📊 Ton Bilan de l'enquête")

# Chargement des données
all_data = load_data(SHEET_URL)

if all_data.empty:
    st.stop()

# --- Identification de l'utilisateur ---
st.header("Retrouve tes résultats")
st.markdown(f"Entre le **code secret** que tu as créé dans le formulaire pour voir tes résultats.")

user_id = st.text_input(f"Ton code secret ({IDENTIFIER_COL}):")

if not user_id:
    st.info("Entre ton code secret ci-dessus pour commencer.")
    st.stop()

# --- Filtrage des données ---
try:
    user_data_row = all_data[all_data[IDENTIFIER_COL].str.lower().str.strip() == user_id.lower().strip()]
except AttributeError:
    user_data_row = all_data[all_data[IDENTIFIER_COL] == user_id]

if user_data_row.empty:
    st.error(f"**Code non trouvé :** Nous n'avons trouvé aucune réponse pour `{user_id}`. Vérifie bien le code.")
    st.stop()

user_data = user_data_row.iloc[0]
user_classifier = user_data[CLASSIFIER_COL]

st.success(f"**Bienvenue !** Nous avons trouvé tes réponses. Tu fais partie du groupe : **{user_classifier}**.")
st.markdown("---")

# --- Affichage des résultats (AVEC ONGLETS) ---
st.header("Tes réponses comparées aux autres")

if user_data_row.empty:
    st.error(f"**Code non trouvé :** Nous n'avons trouvé aucune réponse pour `{user_id}`. Vérifie bien le code.")
    st.stop()

user_data = user_data_row.iloc[0]
user_classifier = user_data[CLASSIFIER_COL]

st.success(f"**Bienvenue !** Nous avons trouvé tes réponses. Tu fais partie du groupe : **{user_classifier}**.")
st.markdown("---")

# --- AFFICHAGE DES RÉSULTATS (Refonte avec boucles) ---
st.header("Tes réponses comparées aux autres")

# --- Section 1: Questions à Échelle (Numériques / Ratings) ---
st.subheader("📊 Questions à échelle (1-10)")

if not SCALE_QUESTIONS:
    st.info("Aucune question de type 'échelle' n'a été configurée.")
else:
    # Créer un onglet pour CHAQUE question numérique
    num_tab_list = st.tabs([f"Question {i+1}" for i in range(len(SCALE_QUESTIONS))])
    
    for i, tab in enumerate(num_tab_list):
        with tab:
            q_col = SCALE_QUESTIONS[i]
            st.markdown(f"**Question :** *{q_col}*")
            
            try:
                user_answer = user_data[q_col]
                if pd.isna(user_answer):
                    st.warning("Tu n'as pas répondu à cette question.")
                else:
                    chart = plot_numerical_comparison(
                        df=all_data,
                        question_col=q_col,
                        classifier_col=CLASSIFIER_COL,
                        user_value=user_answer
                    )
                    st.altair_chart(chart, use_container_width=True)
                    st.markdown(f"La **ligne rouge** montre ta réponse : **{user_answer}**")
            except KeyError:
                st.error(f"⚠️ Oups ! La colonne '{q_col}' n'a pas été trouvée. Vérifiez l'orthographe exacte dans votre liste `SCALE_QUESTIONS`.")
            except Exception as e:
                st.error(f"Erreur d'affichage : {e}")

st.markdown("---")

# --- Section 2: Questions à Choix (Catégoriques) ---
st.subheader("📋 Questions à choix multiples")

if not CATEGORY_QUESTIONS:
    st.info("Aucune question de type 'choix' n'a été configurée.")
else:
    # Créer un onglet pour CHAQUE question catégorique
    cat_tab_list = st.tabs([f"Question {i+1}" for i in range(len(CATEGORY_QUESTIONS))])
    
    for i, tab in enumerate(cat_tab_list):
        with tab:
            q_col = CATEGORY_QUESTIONS[i]
            st.markdown(f"**Question :** *{q_col}*")
            
            try:
                user_answer = user_data[q_col]
                if pd.isna(user_answer):
                    st.warning("Tu n'as pas répondu à cette question.")
                else:
                    chart = plot_categorical_comparison(
                        df=all_data,
                        question_col=q_col,
                        classifier_col=CLASSIFIER_COL,
                        user_value=user_answer
                    )
                    st.altair_chart(chart, use_container_width=True)
                    st.markdown(f"Ta réponse (**{user_answer}**) est affichée en **opaque**. Les autres sont estompées.")
            except KeyError:
                st.error(f"⚠️ Oups ! La colonne '{q_col}' n'a pas été trouvée. Vérifiez l'orthographe exacte dans votre liste `CATEGORY_QUESTIONS`.")
            except Exception as e:
                st.error(f"Erreur d'affichage : {e}")


# --- Données brutes (Optionnel) ---
st.markdown("---")
if st.checkbox("Afficher toutes les données brutes (anonymisées)"):
    # On retire le code secret avant d'afficher
    st.dataframe(all_data.drop(columns=[IDENTIFIER_COL]))