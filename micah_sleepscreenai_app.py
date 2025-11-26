### On Console Cloud Google :
# - Create new project
# - Activate google sheet api
# - Activate google drive api
# - Create new key
# - Download json file of the key
# - Create the corresponding secrets.toml file to connect with an existing gsheet with the wanted column names


# region imports
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from wordcloud import WordCloud
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
# endregion

# region Test de connexion (à supprimer après test)
# try:
#     conn = st.connection("gsheets", type=GSheetsConnection)
#     test_df = conn.read(worksheet="Reponses", ttl=0)
#     st.success("✅ Connexion Google Sheets réussie!")
#     st.dataframe(test_df.head())
# except Exception as e:
#     st.error(f"❌ Erreur de connexion: {e}")
# endregion


# region --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Etude MICAH", layout="centered")


# Load service account info from secrets
service_account_info = st.secrets["gdrive_service_account"]

credentials = Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

client = gspread.authorize(credentials)

SHEET_ID = "1ifQbsvd439slcLIXVlsb0pn0GbAsVMhALHp0hluQS28"
WORKSHEET_NAME = "Reponses"
#sheet = client.open_by_key("1ifQbsvd439slcLIXVlsb0pn0GbAsVMhALHp0hluQS28").worksheet("Reponses")
# endregion

# region --- 2. CSS DESIGN ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; }
    h1, h2, h3, h4, p, label, .stMarkdown, span, div, li {
        color: #FFFFFF !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .css-card {
        background-color: #1E1E1E;
        padding: 25px;
        border-radius: 20px; /* Rounded contours */
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 25px;
        border: 1px solid #333;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #2C2C2C !important;
        color: #FFFFFF !important;
        border: 1px solid #555 !important;
        border-radius: 10px;
    }
    /* Dropdown fix */
    div[data-baseweb="popover"] ul { background-color: #2C2C2C !important; }
    div[data-baseweb="popover"] li > div { color: #FFFFFF !important; }
    div[data-baseweb="popover"] li:hover > div { background-color: #4A90E2 !important; }
    
    .stButton > button {
        width: 100%;
        background-color: #4A90E2;
        color: white !important;
        border: none;
        border-radius: 15px; /* Rounded buttons */
        height: 50px;
        font-size: 16px !important;
        font-weight: 600;
        margin-top: 10px;
        transition: transform 0.1s;
    }
    .stButton > button:hover { transform: scale(1.02); background-color: #357ABD; }
    
    /* Hide standard elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)
# endregion

# region --- 3. LOAD DATA ---
@st.cache_data(ttl=0)
#def load_data():
def load_data(sheet_id, worksheet_name, _gspread_client):
    """Reads the Google Sheet to get data for the graphs."""

    # V1
    # try:
    #     conn = st.connection("gsheets", type=GSheetsConnection)
    #     # ttl=0 ensures we get fresh data every time we reload
    #     df = conn.read(worksheet="Reponses", ttl=0)
    #     return df
    # except Exception as e:
    #     return pd.DataFrame()

    # V2
    try:
        # Re-authorize the sheet using the client passed to the function
        sheet = _gspread_client.open_by_key(sheet_id).worksheet(worksheet_name)

        # Get all records as a list of dicts
        data = sheet.get_all_records()

        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Erreur de chargement des données: {e}")
        return pd.DataFrame()
# endregion

# region--- 3. UTILS FUNCTIONS ---
def save_data_securely(new_data_dict, sheet_id, worksheet_name, _gspread_client):
    """Appends a new row to the Google Sheet."""
    try:
        sheet = _gspread_client.open_by_key(sheet_id).worksheet(worksheet_name)

        # gspread.append_row expects a list of values, in the order of the columns.
        # You'll need to define the exact list of column names (headers)
        # to ensure the data is written correctly.

        # Example: Ensure all columns are present, fill missing ones with None/""
        header = list(new_data_dict.keys())  # Or, define your full list of expected column names
        values_to_append = [new_data_dict.get(col, "") for col in header]  # Get values in order

        sheet.append_row(values_to_append, value_input_option='USER_ENTERED')

        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde: {e}")
        return False

#def save_data_securely(new_data_dict):
    """Reads current data, appends new row, and writes everything back."""
    # try:
    #     conn = st.connection("gsheets", type=GSheetsConnection)
    #
    #     # 1. Read existing data (No Cache)
    #     existing_data = conn.read(worksheet="Reponses", ttl=0)
    #
    #     # 2. Create new row
    #     new_row = pd.DataFrame([new_data_dict])
    #
    #     # 3. Combine old + new
    #     # If existing_data is empty, we just start with new_row
    #     if existing_data.empty:
    #         updated_df = new_row
    #     else:
    #         updated_df = pd.concat([existing_data, new_row], ignore_index=True)
    #
    #     # 4. Write back to sheet
    #     conn.update(worksheet="Reponses", data=updated_df)
    #     return True
    # except Exception as e:
    #     st.error(f"Erreur de sauvegarde: {e}")
    #     return False
    
def get_real_counts(df, category, column, options):
    """Filters the dataframe by category and counts responses for specific options."""
    # Safety check: if data is empty or column missing, return zeros
    if df.empty or column not in df.columns:
        return [0] * len(options) 
    
    # Filter by category (e.g. "Ado" or "Adulte")
    filtered_df = df[df['Category'].astype(str).str.contains(category[:3], case=False, na=False)]
    
    # Count the values
    counts = filtered_df[column].value_counts()
    
    # Ensure every option has a number (even if 0)
    final_counts = counts.reindex(options, fill_value=0).tolist()
    return final_counts

def next_step():
    st.session_state.step += 1
    st.session_state.compare_mode = False # Reset compare toggle for next page

def toggle_compare():
    st.session_state.compare_mode = not st.session_state.compare_mode

def save_to_google_sheets(data):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        new_row = pd.DataFrame([data])
        conn.update(worksheet="Reponses", data=new_row)
        return True
    except Exception as e:
        st.error(f"Erreur technique: {e}")
        return False

# endregion

# region--- 4. GRAPH FUNCTIONS ---
def plot_likert(user_choice, options, data_my_group, data_other_group=None, my_group_name="Mon Groupe", other_group_name="Autre"):
    """
    Generates a horizontal Likert-style bar chart using Plotly.
    """
    fig = go.Figure()

    # 1. My Group Data
    colors = ['#4A90E2'] * len(options) # Default Blue
    
    # Highlight User Choice with Red Border
    line_widths = [0] * len(options)
    line_colors = ['rgba(0,0,0,0)'] * len(options)
    
    if user_choice in options:
        idx = options.index(user_choice)
        colors[idx] = '#FF4B4B' # Red fill for user selection to make it pop
        line_widths[idx] = 3
        line_colors[idx] = '#FFFFFF' # White border

    fig.add_trace(go.Bar(
        y=options,
        x=data_my_group,
        name=my_group_name,
        orientation='h',
        marker=dict(color=colors, line=dict(width=line_widths, color=line_colors), cornerradius=10),
        text=data_my_group,
        textposition='auto'
    ))

    # 2. Comparison Data (Optional)
    if data_other_group:
        fig.add_trace(go.Bar(
            y=options,
            x=data_other_group,
            name=other_group_name,
            orientation='h',
            marker=dict(color='#9B59B6', cornerradius=10), # Purple for others
            text=data_other_group,
            textposition='auto'
        ))

    # 3. Add Arrow Annotation for User Choice
    if user_choice in options:
        idx = options.index(user_choice)
        # We need a rough estimate of the max x value to place the arrow
        max_val = max(data_my_group)
        if data_other_group:
            max_val = max(max_val, max(data_other_group))
            
        fig.add_annotation(
            x=data_my_group[idx],
            y=idx,
            text="Toi",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#FFFFFF",
            ax=40,
            ay=0,
            font=dict(color="white", size=12)
        )

    fig.update_layout(
        plot_bgcolor='#1E1E1E',
        paper_bgcolor='#1E1E1E',
        font=dict(color='white'),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False),
        barmode='group',
        margin=dict(l=0, r=0, t=30, b=0),
        height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='white'))
    )
    return fig

def plot_donut(user_choice, options, data_my_group, data_other_group=None, my_group_name="Mon Groupe"):
    """
    Generates a Ring Plot (Donut) for percentages.
    """
    # Calculate percentages
    total = sum(data_my_group)
    values = data_my_group
    
    # Pull out the slice selected by the user
    pull = [0.1 if opt == user_choice else 0 for opt in options]

    fig = go.Figure(data=[go.Pie(
        labels=options, 
        values=values, 
        hole=.6, # Makes it a donut
        pull=pull, # Explode user choice
        marker=dict(colors=['#4A90E2', '#50E3C2', '#9B59B6']),
        textinfo='label+percent',
        hoverinfo='label+value'
    )])

    # Center text
    fig.add_annotation(text=f"Ton Choix:<br>{user_choice}", x=0.5, y=0.5, font_size=14, showarrow=False, font_color="white")

    fig.update_layout(
        plot_bgcolor='#1E1E1E',
        paper_bgcolor='#1E1E1E',
        font=dict(color='white'),
        margin=dict(l=0, r=0, t=0, b=0),
        height=300,
        showlegend=False
    )
    return fig

# endregion


# region --- 5. SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'compare_mode' not in st.session_state:
    st.session_state.compare_mode = False
# endregion

# region --- 6. MAIN APP FLOW ---

with st.container():
    # ==========================
    # region STEP 1: ID
    # ==========================
    if st.session_state.step == 1:
        st.image("./images/image_accueil.png", use_container_width=True)
        st.title("Partage ton avis sur le sommeil, les écrans et les IA")
        #st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("### 1. Identifiez-vous")
        code = st.text_input("Choisissez un pseudo (ex: PIZZA99)")
        role = st.radio("Vous êtes :", ["Ado (11-17 ans)", "Adulte"], index=None)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Commencer"):
            if code and role:
                # Load the data to check for existing pseudos
                st.session_state.sheet_data = load_data(SHEET_ID, WORKSHEET_NAME, client)

                # Check if the pseudo already exists
                if 'Secret_Code' in st.session_state.sheet_data.columns:
                    existing_codes = st.session_state.sheet_data['Secret_Code'].astype(str).str.upper()
                    if code.upper() in existing_codes.values:
                        st.error("Ce pseudo est déjà pris. Veuillez en choisir un autre.")
                    else:
                        # Pseudo is available, proceed
                        st.session_state.responses['Secret_Code'] = code
                        st.session_state.responses['Category'] = role
                        next_step()
                        st.rerun()
                else:
                    # If column doesn't exist yet (empty sheet), proceed
                    st.session_state.responses['Secret_Code'] = code
                    st.session_state.responses['Category'] = role
                    next_step()
                    st.rerun()
            else:
                st.warning("Veuillez remplir tous les champs.")

        if st.button("Voir les résultats"):
            st.session_state.step = 19
        # if st.button("Commencer"):
        #     if code and role:
        #         st.session_state.responses['Secret_Code'] = code
        #         st.session_state.responses['Category'] = role
        #         #st.session_state.sheet_data = load_data()
        #         st.session_state.sheet_data = load_data(SHEET_ID, WORKSHEET_NAME, client)
        #         next_step()
        #         st.rerun()
        #     else:
        #         st.warning("Veuillez remplir tous les champs.")
    # endregion

    # ==========================
    # region STEP 2: SLEEP QUESTION
    # ==========================
    elif st.session_state.step == 2:
        st.progress(6)
        st.title("Habitudes de Sommeil")
        st.image("./images/sommeil_ecran.jpg", use_container_width=True)

        #st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("#### Regardez-vous des écrans avant de dormir ?")
        screens = st.radio("", ["Jamais", "Parfois", "Souvent", "Tous les soirs"], index=None)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            if screens:
                st.session_state.responses['Screen_Habit'] = screens
                next_step()
                st.rerun()
            else:
                st.warning("Choix requis.")
    # endregion

    # ==========================
    # region STEP 3: SLEEP DATA VIZ
    # ==========================
    # STEP 3: SLEEP VIZ (REAL DATA)
    elif st.session_state.step == 3:
        st.progress(12)
        st.title("📊 Résultats : Ecran & Sommeil")
        
        user_role = st.session_state.responses['Category']
        other_role = "Adulte" if user_role.startswith("Ado") else "Ado (11-17 ans)"
        
        # --- NEW REAL DATA LOGIC ---
        options = ["Jamais", "Parfois", "Souvent", "Tous les soirs"]
        
        # Get counts from the loaded sheet data
        my_counts = get_real_counts(st.session_state.sheet_data, user_role, 'Screen_Habit', options)
        
        # Get comparison counts if mode is active
        other_counts = get_real_counts(st.session_state.sheet_data, other_role, 'Screen_Habit', options) if st.session_state.compare_mode else None
        
        st.markdown(f"<div class='css-card'><h4>Votre groupe : {user_role}</h4>", unsafe_allow_html=True)
        # Use 'my_counts' instead of 'my_data'
        fig = plot_likert(st.session_state.responses['Screen_Habit'], options, my_counts, other_counts, user_role, other_role)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        # ---------------------------

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Comparer Groupes"):
                toggle_compare()
                st.rerun()
        with col2:
            if st.button("Continuer ➡️"):
                next_step()
                st.rerun()
    # endregion

    # ==========================
    # region STEP 4: FACTS (INTERVENTION)
    # ==========================
    elif st.session_state.step == 4:
        st.progress(18)
        st.title("Point Info")
        #st.image("https://i.imgur.com/F0gQ2Zq.png", caption="Cycle du Sommeil", use_container_width=True) #

        
        st.markdown("""
        <div class='css-card'>
            <h3>Le saviez-vous ?</h3>
            <p><strong>La Lumière Bleue</strong><br>
            L'exposition prolongée retarde la sécrétion de mélatonine d'environ 1 heure.<br>
            Ainsi, regarder par exemple votre smartphone peut retarder votre endormissement.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Chart from previous request (Static Matplotlib for the "Study Data")
        st.markdown("<div class='css-card'><h4>Données de l'étude MICAH</h4><p>Voici les résultats de la cohorte MICAH concernant les activités avant l'endormissement.</p>", unsafe_allow_html=True)
        #st.image("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", use_container_width=True)
        
        activities = ['Envoyer des messages aux ami.e.s', 'Vérifier les réseaux sociaux', 'Regarder des vidéos sur Youtube', 'Lire sur un livre/kindle', 'Jouer à des jeux vidéo hors ligne', 'Jouer à des jeux non numériques', 'Publier sur les réseaux sociaux']
        percentages = [81.03, 77.97, 75.18, 66.73, 42.81, 41.10, 39.57]
        sorted_indices = np.argsort(percentages)
        activities = [activities[i] for i in sorted_indices]
        percentages = [percentages[i] for i in sorted_indices]

        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor('#1E1E1E')
        ax.set_facecolor('#1E1E1E')
        bars = ax.barh(activities, percentages, color='#4A90E2', height=0.6)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white', length=0)
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height()/2, f'{width}%', ha='left', va='center', color='white', fontsize=9)
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            next_step()
            st.rerun()
    # endregion


    # ==========================
    # region STEP 5: AI QUESTION
    # ==========================
    elif st.session_state.step == 5:
        st.progress(24)
        st.title("Utilisation des Intelligences Artificielles (IA)")
        st.image("https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", use_container_width=True) # 

        st.markdown("#### A quelle fréquence utilisez-vous l'IA ?")
        #ai_freq = st.select_slider("", options=["Jamais", "Rarement", "Hebdomadaire", "Souvent", "Tous les jours"])
        ai_freq = st.radio("", options=["Jamais", "Rarement", "Hebdomadaire", "Souvent", "Tous les jours"])

        st.markdown("#### Dans quel but ?", unsafe_allow_html=True)
        ai_purpose = st.multiselect("", ["Travail / Devoirs", "Loisirs", "Recherche d'info", "Compagnon virtuel", "Soutien psychologique", "Autre"])
        
        ai_other_text = ""
        if "Autre" in ai_purpose:
            ai_other_text = st.text_input("Précisez pour 'Autre' :")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            final_purpose_list = [p for p in ai_purpose if p != "Autre"]
            if ai_other_text: final_purpose_list.append(ai_other_text) # Just store text for wordcloud later
            
            st.session_state.responses['AI_Freq'] = ai_freq
            st.session_state.responses['AI_Purpose'] = ", ".join(final_purpose_list)
            st.session_state.responses['AI_Wordcloud_Input'] = f'{" ".join(final_purpose_list)} {ai_other_text}' if ai_other_text else " ".join(final_purpose_list) # Dummy default
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 6: AI DATA VIZ
    # ==========================
    elif st.session_state.step == 6:
        st.progress(30)
        st.title("📊 Usage de l'IA")
        
        user_role = st.session_state.responses['Category']
        other_role = "Adulte" if user_role.startswith("Ado") else "Ado (11-17 ans)"
        
        # --- NEW REAL DATA LOGIC ---
        options = ["Jamais", "Rarement", "Hebdomadaire", "Souvent", "Tous les jours"]
        
        my_counts = get_real_counts(st.session_state.sheet_data, user_role, 'AI_Freq', options)
        other_counts = get_real_counts(st.session_state.sheet_data, other_role, 'AI_Freq', options) if st.session_state.compare_mode else None
        
        st.markdown("<div class='css-card'><h4>Fréquence d'utilisation</h4>", unsafe_allow_html=True)
        fig_freq = plot_likert(st.session_state.responses['AI_Freq'], options, my_counts, other_counts, user_role, other_role)
        st.plotly_chart(fig_freq, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        # ---------------------------
        
        # Wordcloud logic - Aggregate ALL responses
        st.markdown("<div class='css-card'><h4>Nuage de mots</h4>", unsafe_allow_html=True)
        #text = st.session_state.responses.get('AI_Wordcloud_Input', '') * 5
        #text = st.session_state.responses.get('AI_Wordcloud_Input', '')

        # Get all AI_Wordcloud_Input responses from the sheet
        if not st.session_state.sheet_data.empty and 'AI_Wordcloud_Input' in st.session_state.sheet_data.columns:
            # Filter by user's category (optional - remove if you want ALL responses regardless of category)
            filtered_df = st.session_state.sheet_data[
                st.session_state.sheet_data['Category'].astype(str).str.contains(user_role[:3], case=False, na=False)
            ]

            # Combine all text from the column
            all_text = ' '.join(filtered_df['AI_Wordcloud_Input'].dropna().astype(str).tolist())

            # Add current user's response
            all_text += ' ' + st.session_state.responses.get('AI_Wordcloud_Input', '')
        else:
            # Fallback to just current user's response if sheet is empty
            all_text = st.session_state.responses.get('AI_Wordcloud_Input', 'Travail Loisirs')

        # Generate wordcloud
        if all_text.strip():  # Only generate if there's text
            wordcloud = WordCloud(width=800, height=400, background_color='#1E1E1E', colormap='Blues').generate(all_text)
            fig_wc, ax = plt.subplots()
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis("off")
            fig_wc.patch.set_facecolor('#1E1E1E')
            st.pyplot(fig_wc)
        else:
            st.info("Pas encore assez de données pour générer un nuage de mots.")

        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Comparer"):
                toggle_compare()
                st.rerun()
        with col2:
            if st.button("Continuer ➡️"):
                next_step()
                st.rerun()
    # endregion

    # ==========================
    # region STEP 7: Ad intermediate
    # ==========================
    elif st.session_state.step == 7:
        st.progress(33)
        st.title("Participe à l'étude Well-Play")

    # --- Texte Streamlit ---
        st.markdown("""
        📱Joue pour la science et soutiens la planète!

        Rejoins l’étude Well-Play sur les jeux vidéo, le bien-être et l’apprentissage.

        🎁 Jusqu’à 60 CHF en bons Galaxus pour toi et 40 CHF pour une asso écologique de ton choix

        ✅ **Demande à un parent de t'y inscrire: **:**

        🔗 [https://well-play-teen.org](https://well-play-teen.org)

        Pour toute question, contactez : [**wellplay@unige.ch**](mailto:wellplay@unige.ch)
        """, unsafe_allow_html=True)

        # See results
        if st.button("Continuer ➡️"):
            next_step()
            st.rerun()


    # ==========================
    # region STEP 8: AI benefit
    # ==========================
    elif st.session_state.step == 8:
        st.progress(36)
        st.title("Bénéfices des Intelligences Artificielles")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        #st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("#### Quels sont les avantages (bénéfices?) de l'IA pour vous ?")
        ai_benefit = st.multiselect("", ["Pratique / Utile", "Rapide", "Ne me juge pas", "Suscite l'inspiration",
                                         "Sentiment d'accomplissement", "Pas de bénéfices", "Autre"])

        ai_other_text = ""
        if "Autre" in ai_benefit:
            ai_other_text = st.text_input("Précisez pour 'Autre' :")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            final_purpose_list = [p for p in ai_benefit if p != "Autre"]
            if ai_other_text: final_purpose_list.append(ai_other_text)  # Just store text for wordcloud later

            st.session_state.responses['AI_Benefit'] = ", ".join(final_purpose_list)
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 9: AI benefit scale
    # ==========================
    elif st.session_state.step == 9:
        st.progress(42)
        st.title("Avantages des Intelligences Artificielles")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        #st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("#### Dans quelle mesure pensez-vous que les IA apportent des avantages ?")
        ai_benefit_scale = st.select_slider("", options=list(range(1, 11)), value=5)
        # Custom labels below the slider
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.write("**Les IA n'apportent aucun avantages**")
        with col3:
            st.write("**Les IA apporteront toujours des avantages**")


        if st.button("Continuer ➡️"):
            st.session_state.responses['AI_Benefit_Scale'] = ai_benefit_scale
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 10: FEELINGS QUESTION
    # ==========================
    elif st.session_state.step == 10:
        st.progress(48)
        st.title("Emotions & Intelligences Artificielles")
        st.image("https://images.unsplash.com/photo-1516387938699-a93567ec168e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", use_container_width=True)
        #st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("#### Avez-vous déjà parlé de vos sentiments avec une IA ?")
        chatgpt_feelings = st.radio("", ["Oui", "Non", "Je ne sais pas"], horizontal=False)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            st.session_state.responses['ChatGPT_Feelings'] = chatgpt_feelings
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 11: IA feeling viz
    # ==========================

    elif st.session_state.step == 11:
        st.progress(60)
        st.title("Émotions & IA")

        user_role = st.session_state.responses['Category']

        # --- NEW REAL DATA LOGIC ---
        options = ["Oui", "Non", "Je ne sais pas"]
        my_counts = get_real_counts(st.session_state.sheet_data, user_role, 'ChatGPT_Feelings', options)
        #st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        fig_donut = plot_donut(st.session_state.responses['ChatGPT_Feelings'], options, my_counts)
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            next_step()
            st.rerun()
        # ---------------------------

    # endregion


    # ==========================
    # region STEP 12: AI level of concern scale
    # ==========================
    elif st.session_state.step == 12:
        st.progress(66)
        st.title("Préoccupation des Intelligence Artificielles")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        st.markdown("#### Dans quelle mesure êtes-vous préoccupé.e.s par les IA ?")
        ai_concern_scale = st.select_slider("", options=list(range(1, 11)), value=5)
        # Custom labels below the slider
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.write("**Les IA ne me causent aucun souci**")
        with col3:
            st.write("**Les IA me causent beaucoup d'inquiétude**")

        if st.button("Continuer ➡️"):
            st.session_state.responses['AI_Concern_Scale'] = ai_concern_scale
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 13: AI Concern Items
    # ==========================
    elif st.session_state.step == 13:
        st.progress(72)
        st.title("Inquiétudes et Intelligences Artificielles")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)

        st.markdown("#### Quels sont vos inquiétudes par rapport à l'IA ?")
        ai_concern_items = st.multiselect("", ["Perte des capacités de réflexion critique", "Impact sur les générations futures", "Impact sur les industries artistiques et créatives", "Désinformation/mésinformation",
                                         "Impact sur le marché du travail", "Impact sur l'environnement","Manque de confidentialité et de protection des données", "Je n'ai aucune inquiétude", "Autre"])

        ai_other_text = ""
        if "Autre" in ai_concern_items:
            ai_other_text = st.text_input("Précisez pour 'Autre' :")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            final_purpose_list = [p for p in ai_concern_items if p != "Autre"]
            if ai_other_text: final_purpose_list.append(ai_other_text)  # Just store text for wordcloud later

            st.session_state.responses['AI_Concern_Items'] = ", ".join(final_purpose_list)
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 14: AI Responsible People
    # ==========================
    elif st.session_state.step == 14:
        st.progress(78)
        st.title("Responsabilité & Intelligences Artificielles")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)

        st.markdown("#### Selon vous, qui est le plus responsable de l'enseignement des compétences dans les IA ?")
        ai_responsible_people = st.multiselect("", ["Moi-même",
                                               "Mes proches (amis, frères, soeurs)",
                                               "L'école (ienseignants, bibliothécaires)",
                                               "L'IA elle-même",
                                               "Les grandes entreprise de la Tech (Tech companies)",
                                               "Les parents / éducateurs",
                                               "Des experts (chercheurs)",
                                               "Le gouvernement", "Autre"])

        ai_other_text = ""
        if "Autre" in ai_responsible_people:
            ai_other_text = st.text_input("Précisez pour 'Autre' :")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            final_purpose_list = [p for p in ai_responsible_people if p != "Autre"]
            if ai_other_text: final_purpose_list.append(ai_other_text)  # Just store text for wordcloud later

            st.session_state.responses['AI_Responsible_People'] = ", ".join(final_purpose_list)
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 15: AI Features
    # ==========================
    elif st.session_state.step == 15:
        st.progress(84)
        st.title("Fonctionnalité & Intelligences Artificielles")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)
        st.markdown("#### Quelle fonctionnalité aimeriez-vous implémenter dans l'IA ?")
        ai_feature = st.text_input("Ecrivez toutes vos idées", key = "ai_feature")

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            st.session_state.responses['AI_Feature'] = ai_feature
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 16: AI Prevention Campaign
    # ==========================
    elif st.session_state.step == 16:
        st.progress(90)
        st.title("Prévention & Intelligences Artificielles")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)
        st.markdown("#### Les campagnes de prévention sont trop sérieuses, parmi les éléments suivants, lesquels t’aideraient à mieux comprendre les informations sur la bonne utilisation et la sécurité des IA?")
        ai_prevention_campaign = st.multiselect("", ["Des explications plus simples et claires",
                                                    "Des vidéos courtes ou des tutoriels",
                                                    "Des influenceurs/ambassadeurs qui en parlent",
                                                    "Des ateliers ou démonstrations en classe",
                                                    "Des illustrations (publicités nationales radio/tv/réseaux sociaux)",
                                                    "Autre"])

        ai_other_text = ""
        if "Autre" in ai_prevention_campaign:
            ai_other_text = st.text_input("Précisez pour 'Autre' :", key="ai_other_text")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            final_purpose_list = [p for p in ai_prevention_campaign if p != "Autre"]
            if ai_other_text: final_purpose_list.append(ai_other_text)  # Just store text for wordcloud later

            st.session_state.responses['AI_Prevention_Campaign'] = ", ".join(final_purpose_list)
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 17: Give comment
    # ==========================
    elif st.session_state.step == 17:
        st.progress(96)
        st.title("Exprimez-vous")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)
        st.markdown("#### Laissez-nous vos remarques et commentaires :")
        ai_comments = st.text_input("")

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            st.session_state.responses['AI_Comments'] = ai_comments
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 18: SUBMIT
    # =========================
    elif st.session_state.step == 18:
        st.image("./images/image_accueil.png", use_container_width=True)

        # Initialize a flag to track if data was already submitted
        if 'data_submitted' not in st.session_state:
            st.session_state.data_submitted = False

        if not st.session_state.data_submitted:
            if st.button("Envoyer mes réponses"):
                with st.spinner("Envoi en cours..."):
                    #success = save_to_google_sheets(st.session_state.responses)

                    # Add timestamp
                    st.session_state.responses['Timestamp'] = datetime.now().isoformat()
                    success = save_data_securely(st.session_state.responses, SHEET_ID, WORKSHEET_NAME, client)
                    if success:
                        st.session_state.data_submitted = True
                        st.rerun()
                    else:
                        st.error("Erreur de sauvegarde.")
        else:
            # Data has been submitted, show success message
            st.success("Merci ! Vos réponses ont été enregistrées.")
            st.balloons()
            next_step()
            st.rerun()

            #if st.button("Accéder à mes réponses"):
            #if st.button("Terminer"):
             #   next_step()
              #  st.rerun()

    # ==========================
    # region STEP 19: Ad final
    # ==========================
    elif st.session_state.step == 19:
        st.progress(100)
        st.title("Merci pour votre participation !")


        # --- Texte Streamlit ---
        st.markdown("""
        <div class='css-card'>
        <h3>👋 Tu as entre 11 et 15 ans ?</h3>
        <p>Participe à Well-Play, une étude scientifique de l'UNIGE et de la HedS sur le lien entre jeux vidéo, bien-être et apprentissage – que tu joues aux jeux vidéo ou pas.</p>

        <ul>
            <li>Pour tous les ados de 11 à 15 ans</li>
            <li>40 CHF pour l'association écologique de ton choix</li>
            <li>Jusqu'à 60 CHF en bons Galaxus pour toi</li>
        </ul>

        <h3>👨‍👩‍👧 Pour participer</h3>
        <p>Montre ce message à un de tes parents ou envoie-lui le lien sur WhatsApp (tu peux aussi le partager à un·e ami·e) :</p>
        <p>🔗 <a href="https://well-play-teen.org">https://well-play-teen.org</a></p>

        <p>Pour toute question, contactez : <a href="mailto:wellplay@unige.ch"><strong>wellplay@unige.ch</strong></a></p>

        </div>
        """, unsafe_allow_html=True)


       # See results
        #if st.button("Terminer"):
        # if st.button("Voir les résultats"):
        #     next_step()
        #     st.rerun()

    # ==========================
    # region STEP 19: See results
    # ==========================
    elif st.session_state.step == 19:
        st.title("Résumé de vos réponses")
        st.markdown("### Voici un aperçu de ce que vous avez répondu :")
        st.markdown("Cette page est en cours de construction. Elle arrive bientôt.")

        # region Charger les données et afficher les noms des colonnes
        #@st.cache_data(ttl=60)
        def load_data_to_see_results():
            SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRCbQDPet7-hUdVO0-CzfC3KrhHY6JbUO4UlMpUwbJJ_cp2LhqJSnX34jD-xqZcFAmI4FZZcEg9Wsuj/pub?output=csv"
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
        # endregion

        # region Utils Functions

        # Simplifier les labels pour l'affichage
        def simplify_category(category):
            if pd.isna(category):
                return "Non spécifié"
            elif "ado" in category.lower():
                return "Adolescents (11-17 ans)"
            elif "adulte" in category.lower():
                return "Adultes"
            else:
                return category
        # endregion

        # region Graph Functions
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


        # Fonction pour créer un graphique d'échelle numérique
        def create_numeric_scale_chart(data, question_col, title, participant_answer=None):
            """
            Crée un graphique en barres pour une échelle numérique (1-10)
            """
            # Compter les réponses
            counts = data[question_col].value_counts().sort_index()

            # S'assurer que toutes les valeurs de 1 à 10 sont présentes
            all_values = pd.Series(0, index=range(1, 11))
            for value, count in counts.items():
                if 1 <= value <= 10:
                    all_values[value] = count

            # Calculer les pourcentages
            percentages = (all_values / len(data)) * 100

            fig, ax = plt.subplots(figsize=(14, 8))

            # Définir un gradient de couleurs du vert (peu préoccupé) au rouge (très préoccupé)
            colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, 10))

            # Créer les barres
            bars = ax.bar(range(1, 11), percentages.values, color=colors, alpha=0.7,
                          edgecolor='black', linewidth=1)

            # Mettre en évidence la réponse du participant
            if participant_answer is not None and 1 <= participant_answer <= 10:
                bars[int(participant_answer) - 1].set_edgecolor('red')
                bars[int(participant_answer) - 1].set_linewidth(4)
                bars[int(participant_answer) - 1].set_alpha(1.0)

            # Personnaliser le graphique
            ax.set_xlabel('Niveau de préoccupation (1 = Pas du tout, 10 = Extrêmement)',
                          fontsize=12, fontweight='bold')
            ax.set_ylabel('Pourcentage des réponses (%)', fontsize=12, fontweight='bold')
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xticks(range(1, 11))

            # Ajouter les valeurs sur les barres
            for i, (bar, count, pct) in enumerate(zip(bars, all_values.values, percentages.values)):
                if count > 0:  # N'afficher que si il y a des réponses
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                            f'{count}\n({pct:.1f}%)',
                            ha='center', va='bottom', fontweight='bold', fontsize=9)

            # Améliorer l'apparence
            ax.set_ylim(0, max(percentages.values) * 1.2 if max(percentages.values) > 0 else 10)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            plt.tight_layout()
            return fig


        # Fonction pour créer un graphique de comparaison par catégorie d'âge
        def create_age_category_comparison_chart(data, question_col, category_col, title):
            """
            Crée un graphique comparant les réponses entre adolescents et adultes
            """
            # Filtrer les données valides (réponses de 1 à 10)
            valid_data = data[
                (data[question_col].between(1, 10)) &
                (data[category_col].notna())
                ].copy()

            if len(valid_data) == 0:
                return None

            valid_data['Groupe_Simple'] = valid_data[category_col].apply(simplify_category)

            # Calculer les moyennes par groupe
            avg_by_group = valid_data.groupby('Groupe_Simple')[question_col].agg(['mean', 'count', 'std']).round(2)

            # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
            fig, ax1 = plt.subplots(1, 1, figsize=(16, 10))

            # Graphique 1: Moyennes par groupe avec barres d'erreur
            colors = ['#ff7f50', '#4682b4']  # Orange pour ados, Bleu pour adultes
            bars1 = ax1.bar(avg_by_group.index, avg_by_group['mean'],
                            color=colors[:len(avg_by_group)], alpha=0.7,
                            edgecolor='black', linewidth=1,
                            yerr=avg_by_group['std'], capsize=5)

            ax1.set_ylabel('Niveau moyen de préoccupation', fontsize=11, fontweight='bold')
            ax1.set_title('Niveau moyen de préoccupation par groupe', fontsize=12, fontweight='bold')
            ax1.set_ylim(0, 10)
            ax1.grid(axis='y', alpha=0.3, linestyle='--')

            # Rotation des labels si nécessaire
            ax1.tick_params(axis='x', rotation=45)

            # Ajouter les valeurs sur les barres
            for i, (bar, (idx, row)) in enumerate(zip(bars1, avg_by_group.iterrows())):
                ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                         f'{row["mean"]:.1f}\n(n={int(row["count"])})',
                         ha='center', va='bottom', fontweight='bold', fontsize=10)

            # Graphique 2: Distribution détaillée
            # groups = valid_data['Groupe_Simple'].unique()
            # if len(groups) >= 2:
            #     data_by_group = [valid_data[valid_data['Groupe_Simple'] == group][question_col]
            #                      for group in sorted(groups)]
            #
            #     bins = np.arange(0.5, 11.5, 1)
            #     ax2.hist(data_by_group, bins=bins, alpha=0.7,
            #              label=sorted(groups), color=colors[:len(groups)],
            #              edgecolor='black')
            #     ax2.set_xlabel('Niveau de préoccupation', fontsize=11, fontweight='bold')
            #     ax2.set_ylabel('Nombre de réponses', fontsize=11, fontweight='bold')
            #     ax2.set_title('Distribution des réponses par groupe', fontsize=12, fontweight='bold')
            #     ax2.set_xticks(range(1, 11))
            #     ax2.legend()
            #     ax2.grid(axis='y', alpha=0.3, linestyle='--')

            plt.tight_layout()
            return fig


        # Fonction pour créer comparaison de wordcloud graphique
        def create_wordcloud_comparison(data, text_col, category_col):
            """
            Crée des word clouds comparatifs pour adolescents et adultes
            """

            # Préparer les données
            valid_data = data[(data[text_col].notna()) & (data[category_col].notna())].copy()
            valid_data['Groupe_Simple'] = valid_data[category_col].apply(simplify_category)

            # Séparer les réponses par groupe
            adolescents_text = valid_data[valid_data['Groupe_Simple'] == 'Adolescents'][text_col]
            adultes_text = valid_data[valid_data['Groupe_Simple'] == 'Adultes'][text_col]

            if len(adolescents_text) == 0 and len(adultes_text) == 0:
                return None, None

            # Nettoyer et combiner le texte pour chaque groupe
            def clean_and_combine_text(text_series):
                if len(text_series) == 0:
                    return ""

                # Combiner tous les textes
                combined_text = ' '.join(text_series.astype(str))

                # Nettoyer le texte (optionnel - vous pouvez ajuster selon vos besoins)
                combined_text = re.sub(r'[^\w\s]', ' ', combined_text)  # Supprimer la ponctuation
                combined_text = re.sub(r'\s+', ' ', combined_text)  # Normaliser les espaces

                return combined_text.lower()

            adolescents_combined = clean_and_combine_text(adolescents_text)
            adultes_combined = clean_and_combine_text(adultes_text)

            # Créer les word clouds
            wordcloud_kwargs = {
                'width': 800,
                'height': 400,
                'background_color': 'white',
                'max_words': 100,
                'relative_scaling': 0.5,
                'min_font_size': 10
            }

            wc_adolescents = None
            wc_adultes = None

            if adolescents_combined.strip():
                wc_adolescents = WordCloud(**wordcloud_kwargs, colormap='Oranges').generate(adolescents_combined)

            if adultes_combined.strip():
                wc_adultes = WordCloud(**wordcloud_kwargs, colormap='Blues').generate(adultes_combined)

            return wc_adolescents, wc_adultes


        def plot_wordclouds(wc_adolescents, wc_adultes, adolescents_count, adultes_count):
            """
            Affiche les word clouds côte à côte
            """
            # Déterminer le nombre de subplots nécessaires
            valid_clouds = sum([wc_adolescents is not None, wc_adultes is not None])

            if valid_clouds == 0:
                st.warning("Aucun word cloud ne peut être généré - données textuelles insuffisantes")
                return None

            if valid_clouds == 1:
                fig, ax = plt.subplots(1, 1, figsize=(12, 6))
                axes = [ax]
            else:
                fig, axes = plt.subplots(1, 2, figsize=(16, 8))

            current_ax = 0

            # Word cloud des adolescents
            if wc_adolescents is not None:
                axes[current_ax].imshow(wc_adolescents, interpolation='bilinear')
                axes[current_ax].set_title(f'🧑‍🎓 Adolescents (n={adolescents_count})',
                                           fontsize=14, fontweight='bold', color='#ff7f50')
                axes[current_ax].axis('off')
                current_ax += 1

            # Word cloud des adultes
            if wc_adultes is not None:
                ax_index = current_ax if valid_clouds == 2 else 0
                axes[ax_index].imshow(wc_adultes, interpolation='bilinear')
                axes[ax_index].set_title(f'👨‍👩‍👧‍👦 Adultes (n={adultes_count})',
                                         fontsize=14, fontweight='bold', color='#4682b4')
                axes[ax_index].axis('off')

            plt.tight_layout()
            return fig


        def create_donut_comparison(data, question_col, category_col):
            """
            Crée des graphiques en donut comparatifs pour adolescents et adultes
            """

            # Préparer les données
            valid_data = data[(data[question_col].notna()) & (data[category_col].notna())].copy()
            valid_data['Groupe_Simple'] = valid_data[category_col].apply(simplify_category)

            # Séparer les données par groupe
            adolescents_data = valid_data[valid_data['Groupe_Simple'] == 'Adolescents'][question_col]
            adultes_data = valid_data[valid_data['Groupe_Simple'] == 'Adultes'][question_col]

            # Cette colonne peut contenir plusieurs réponses séparées par des virgules
            # On va les séparer et compter chaque élément
            def process_multiple_answers(data_series):
                if len(data_series) == 0:
                    return {}

                all_answers = []
                for response in data_series:
                    if pd.notna(response):
                        # Séparer les réponses multiples (supposant qu'elles sont séparées par des virgules)
                        answers = [answer.strip() for answer in str(response).split(',')]
                        all_answers.extend(answers)
                # Compter les occurrences
                return Counter(all_answers)

            adolescents_counts = process_multiple_answers(adolescents_data)
            adultes_counts = process_multiple_answers(adultes_data)

            return adolescents_counts, adultes_counts


        def plot_donut_charts(adolescents_counts, adultes_counts):
            """
            Affiche les graphiques en donut côte à côte
            """
            # Vérifier s'il y a des données
            if not adolescents_counts and not adultes_counts:
                st.warning("Aucune donnée disponible pour créer les graphiques")
                return None

            # Déterminer le nombre de graphiques à afficher
            charts_to_show = []
            if adolescents_counts:
                charts_to_show.append(('Adolescents', adolescents_counts, '#ff7f50'))
            if adultes_counts:
                charts_to_show.append(('Adultes', adultes_counts, '#4682b4'))

            if len(charts_to_show) == 0:
                return None

            # Créer la figure
            if len(charts_to_show) == 1:
                fig, ax = plt.subplots(1, 1, figsize=(10, 8))
                axes = [ax]
            else:
                fig, axes = plt.subplots(1, 2, figsize=(16, 8))

            for i, (group_name, counts, base_color) in enumerate(charts_to_show):
                ax = axes[i] if len(charts_to_show) > 1 else axes[0]

                # Préparer les données pour le graphique
                labels = list(counts.keys())
                sizes = list(counts.values())
                total_responses = sum(sizes)

                # Tronquer les labels trop longs pour l'affichage
                display_labels = []
                for label in labels:
                    if len(label) > 30:
                        display_labels.append(label[:27] + "...")
                    else:
                        display_labels.append(label)

                # Créer une palette de couleurs basée sur la couleur de base
                if base_color == '#ff7f50':  # Orange pour adolescents
                    colors = plt.cm.Oranges(np.linspace(0.4, 0.8, len(sizes)))
                else:  # Bleu pour adultes
                    colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(sizes)))

                # Créer le donut chart
                wedges, texts, autotexts = ax.pie(
                    sizes,
                    labels=display_labels,
                    colors=colors,
                    autopct=lambda pct: f'{pct:.1f}%\n({int(pct / 100 * total_responses)})',
                    startangle=90,
                    pctdistance=0.85,
                    wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2)
                )

                # Personnaliser le texte
                for autotext in autotexts:
                    autotext.set_color('black')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(9)

                for text in texts:
                    text.set_fontsize(10)
                    text.set_fontweight('bold')

                # Ajouter le titre avec emoji approprié
                emoji = "🧑‍🎓" if group_name == "Adolescents" else "👨‍👩‍👧‍👦"
                ax.set_title(f'{emoji} {group_name}\n({total_responses} réponses)',
                             fontsize=14, fontweight='bold', pad=20)

                # Ajouter le texte au centre du donut
                ax.text(0, 0, f'{total_responses}\nréponses',
                        horizontalalignment='center', verticalalignment='center',
                        fontsize=12, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

            plt.tight_layout()
            return fig
        # endregion

        # region Section pour le code secret
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

        # endregion

        # region Graphique Likert pour les écrans avant de dormir
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

        # endregion







        if st.button("Terminer"):
            st.session_state.step = 1
            st.session_state.responses = {}
            st.rerun()
