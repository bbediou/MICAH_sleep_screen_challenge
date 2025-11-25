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

        if st.button("J'ai compris"):
            next_step()
            st.rerun()
    # endregion


    # ==========================
    # region STEP 5: AI QUESTION
    # ==========================
    elif st.session_state.step == 5:
        st.progress(24)
        st.title("L'Intelligence Artificielle")
        st.image("https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", use_container_width=True) # 

        
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
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
        
        # Wordcloud logic (Safe default)
        st.markdown("<div class='css-card'><h4>Nuage de mots</h4>", unsafe_allow_html=True)
        #text_base = "Travail Devoirs Recherche Fun Loisirs "
        #text = text_base + st.session_state.responses.get('AI_Wordcloud_Input', '') * 5
        #text = st.session_state.responses.get('AI_Wordcloud_Input', '') * 5
        text = st.session_state.responses.get('AI_Wordcloud_Input', '')

        wordcloud = WordCloud(width=800, height=400, background_color='#1E1E1E', colormap='Blues').generate(text)
        fig_wc, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        fig_wc.patch.set_facecolor('#1E1E1E')
        st.pyplot(fig_wc)
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
    # region STEP 7: AI benefit
    # ==========================
    elif st.session_state.step == 7:
        st.progress(36)
        st.title("L'Intelligence Artificielle")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
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
    # region STEP 8: AI benefit scale
    # ==========================
    elif st.session_state.step == 8:
        st.progress(42)
        st.title("L'Intelligence Artificielle")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
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
    # region STEP 9: FEELINGS QUESTION
    # ==========================
    elif st.session_state.step == 9:
        st.progress(48)
        st.title("Finalisation")
        st.image("https://images.unsplash.com/photo-1516387938699-a93567ec168e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", use_container_width=True) #


        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("#### Avez-vous déjà parlé de vos sentiments avec une IA ? [cite: 129]")
        chatgpt_feelings = st.radio("", ["Oui", "Non", "Je ne sais pas"], horizontal=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            st.session_state.responses['ChatGPT_Feelings'] = chatgpt_feelings
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 10: IA feeling viz
    # ==========================

    elif st.session_state.step == 10:
        st.progress(60)
        st.title("❤️ IA & Émotions")

        user_role = st.session_state.responses['Category']

        # --- NEW REAL DATA LOGIC ---
        options = ["Oui", "Non", "Je ne sais pas"]
        my_counts = get_real_counts(st.session_state.sheet_data, user_role, 'ChatGPT_Feelings', options)

        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        fig_donut = plot_donut(st.session_state.responses['ChatGPT_Feelings'], options, my_counts)
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            next_step()
            st.rerun()
        # ---------------------------

    # endregion


    # ==========================
    # region STEP 11: AI level of concern scale
    # ==========================
    elif st.session_state.step == 11:
        st.progress(66)
        st.title("L'Intelligence Artificielle")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
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
    # region STEP 12: AI Concern Items
    # ==========================
    elif st.session_state.step == 12:
        st.progress(72)
        st.title("L'Intelligence Artificielle")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
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
    # region STEP 13: AI Responsible People
    # ==========================
    elif st.session_state.step == 13:
        st.progress(78)
        st.title("L'Intelligence Artificielle")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
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
    # region STEP 14: AI Features
    # ==========================
    elif st.session_state.step == 14:
        st.progress(84)
        st.title("L'Intelligence Artificielle")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("#### Quelle fonctionnalité aimeriez-vous implémenter dans l'IA ?")
        ai_feature = st.text_input("Ecrivez toutes vos idées", key = "ai_feature")

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            st.session_state.responses['AI_Feature'] = ai_feature
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 15: AI Prevention Campaign
    # ==========================
    elif st.session_state.step == 15:
        st.progress(90)
        st.title("L'Intelligence Artificielle")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("#### Les campagnes de prévention sont souvent austères, parmi les éléments suivants, lesquels t’aideraient à mieux comprendre les informations sur la bonne utilisation et la sécurité des IA?")
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
    # region STEP 16: Give comment
    # ==========================
    elif st.session_state.step == 16:
        st.progress(96)
        st.title("Exprimez-vous")
        st.image(
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True)  #

        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.markdown("#### Laissez-nous vos remarques et commentaires :")
        ai_comments = st.text_input("")

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continuer ➡️"):
            st.session_state.responses['AI_Comments'] = ai_comments
            next_step()
            st.rerun()
    # endregion

    # ==========================
    # region STEP 17: SUBMIT
    # =========================
    elif st.session_state.step == 17:
        # Recruitment
        # st.markdown("""
        # <div class='css-card' style='border: 1px solid #FF4B4B;'>
        #     [cite_start]<h4>🎮 Étude Well-Play</h4>
        #     <p>Nous cherchons des jeunes de 11 à 15 ans. Contact: wellplay@unige.ch</p>
        # </div>
        # """, unsafe_allow_html=True)

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
            st.image("https://i.imgur.com/0dZ8ZqZ.png", use_container_width=True)
            st.success("Merci ! Vos réponses ont été enregistrées.")
            st.balloons()

            if st.button("Accéder à mes réponses"):
                next_step()
                st.rerun()

    # ==========================
    # region STEP 18: Ad final
    # ==========================
    elif st.session_state.step == 18:
        st.progress(100)
        st.title("Vos réponses")


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
        if st.button("Voir les résultats"):
            next_step()
            st.rerun()

    # ==========================
    # region STEP 19: See results
    # ==========================
    elif st.session_state.step == 19:
        st.title("Résumé de vos réponses")
        st.markdown("### Voici un aperçu de ce que vous avez répondu :")

        #df = pd.DataFrame.from_dict(st.session_state.responses, orient='index', columns=['Réponse'])
        #st.dataframe(df)

        if st.button("Terminer"):
            st.session_state.step = 1
            st.session_state.responses = {}
            st.rerun()
