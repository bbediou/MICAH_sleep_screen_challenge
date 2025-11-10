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

# Group icons and colors mapping
GROUP_ICONS = {
    "adolescent": "👦",
    "ado": "👦", 
    "teen": "👦",
    "parent": "👨‍👩‍👧",
    "parents": "👨‍👩‍👧",
    "teacher": "👩‍🏫",
    "enseignant": "👩‍🏫",
    "professeur": "👩‍🏫"
}

# Vibrant color scheme inspired by Google Forms
GROUP_COLORS = {
    "adolescent": "#4285F4",  # Google Blue
    "ado": "#4285F4",
    "teen": "#4285F4",
    "parent": "#34A853",      # Google Green
    "parents": "#34A853",
    "teacher": "#EA4335",     # Google Red
    "enseignant": "#EA4335",
    "professeur": "#EA4335"
}

# Default icon and color for unknown groups
DEFAULT_ICON = "👤"
DEFAULT_COLOR = "#9E9E9E"

def get_group_icon(group_name):
    """Get icon for a group, case-insensitive."""
    if pd.isna(group_name):
        return DEFAULT_ICON
    group_lower = str(group_name).lower().strip()
    return GROUP_ICONS.get(group_lower, DEFAULT_ICON)

def get_group_color(group_name):
    """Get color for a group, case-insensitive."""
    if pd.isna(group_name):
        return DEFAULT_COLOR
    group_lower = str(group_name).lower().strip()
    return GROUP_COLORS.get(group_lower, DEFAULT_COLOR)

def get_color_scale(df, classifier_col):
    """Create a color scale mapping for the groups in the dataframe."""
    unique_groups = df[classifier_col].dropna().unique()
    domain = []
    range_colors = []
    
    for group in unique_groups:
        domain.append(group)
        range_colors.append(get_group_color(group))
    
    return alt.Scale(domain=domain, range=range_colors)

# Custom CSS for mobile optimization and better styling
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .stApp {
        max-width: 100%;
        padding: 0;
    }
    
    /* Adjust padding for mobile */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.5rem !important;
        }
        
        /* Make charts responsive */
        .vega-embed {
            width: 100% !important;
        }
        
        /* Smaller headers on mobile */
        h1 {
            font-size: 1.8rem !important;
        }
        h2 {
            font-size: 1.4rem !important;
        }
        h3 {
            font-size: 1.2rem !important;
        }
        
        /* Adjust tab styling for mobile */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.2rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 0.8rem;
            font-size: 0.9rem;
        }
    }
    
    /* Success/error message styling */
    .stSuccess, .stError, .stWarning, .stInfo {
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Input field styling */
    .stTextInput input {
        border-radius: 0.5rem;
        font-size: 1rem;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #4A90E2;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #357ABD;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Card-like sections */
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Custom divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(to right, #4A90E2, #E5E5E5);
        margin: 2rem 0;
        border-radius: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Configuration - CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRCbQDPet7-hUdVO0-CzfC3KrhHY6JbUO4UlMpUwbJJ_cp2LhqJSnX34jD-xqZcFAmI4FZZcEg9Wsuj/pub?output=csv"

# Column configurations
CLASSIFIER_COL = "Tu es :"
IDENTIFIER_COL = "Choisis ton code secret"

SCALE_QUESTIONS = [
    "A quel point ton sommeil est-il réparateur ?",
    "Quelle est la qualité de ton sommeil ?"
]

CATEGORY_QUESTIONS = [
    "As tu des écrans dans ta chambre (smartphone compris) ?",
    'Scénario - "22 h 30"',  # Fixed encoding
    "Regardes-tu ton téléphone dès le réveil ?"
]

# --- DATA LOADING ---
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
        st.error(f"Erreur de chargement des données : {e}")
        return pd.DataFrame()

# --- ENHANCED PLOTTING FUNCTIONS ---

def plot_numerical_comparison(df, question_col, classifier_col, user_value, show_other_groups=True):
    """
    Crée un histogramme amélioré avec un design moderne et mobile-friendly.
    Utilise des bins entiers et met en évidence la réponse de l'utilisateur.
    """
    # Prepare safe column names for Altair
    df_plot = df.copy()
    col_map = {col: (col.replace(':', '\\:') if isinstance(col, str) and ':' in col else col)
               for col in df_plot.columns}
    if any(col_map[c] != c for c in col_map):
        df_plot = df_plot.rename(columns=col_map)

    q_field = col_map.get(question_col, question_col)
    cls_field = col_map.get(classifier_col, classifier_col)

    # Get user's group
    user_group = user_data[classifier_col] if 'user_data' in globals() else None

    # Filter data based on show_other_groups option
    if not show_other_groups and user_group:
        df_plot = df_plot[df_plot[classifier_col] == user_group]

    # Calculate statistics for context
    user_percentile = (df_plot[col_map.get(question_col, question_col)] <= user_value).mean() * 100

    # Round values to integers for binning
    df_plot['rounded_value'] = df_plot[q_field].round().astype(int)
    
    # Get color scale
    color_scale = get_color_scale(df_plot, cls_field)

    # Create aggregated data for histogram
    histogram_data = df_plot.groupby(['rounded_value', cls_field]).size().reset_index(name='count')
    
    # Mark user's response
    histogram_data['is_user_value'] = histogram_data['rounded_value'] == int(round(user_value))

    # Enhanced histogram with proper stacking and colors
    bars = alt.Chart(histogram_data).mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4
    ).encode(
        x=alt.X('rounded_value:O', 
                title=question_col,
                axis=alt.Axis(
                    labelAngle=0,
                    titleFontSize=14,
                    labelFontSize=12,
                    grid=False
                )),
        y=alt.Y('count:Q', 
                stack='zero',
                title="Nombre de réponses",
                axis=alt.Axis(
                    titleFontSize=14,
                    labelFontSize=12,
                    grid=True,
                    gridOpacity=0.3
                )),
        color=alt.Color(f"{cls_field}:N", 
                       title="Type de répondant",
                       scale=color_scale,
                       legend=alt.Legend(
                           orient='bottom',
                           titleFontSize=12,
                           labelFontSize=11
                       )),
        opacity=alt.condition(
            alt.datum.is_user_value,
            alt.value(1.0),
            alt.value(0.5)
        ),
        tooltip=[
            alt.Tooltip('rounded_value:O', title=question_col),
            alt.Tooltip(cls_field, type='nominal', title=classifier_col),
            alt.Tooltip('count:Q', title='Nombre')
        ]
    )

    # Highlight border for user's value
    user_highlight = alt.Chart(histogram_data[histogram_data['is_user_value']]).mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
        stroke='#E53E3E',
        strokeWidth=3,
        fillOpacity=0
    ).encode(
        x=alt.X('rounded_value:O'),
        y=alt.Y('count:Q', stack='zero'),
        color=alt.Color(f"{cls_field}:N", scale=color_scale, legend=None)
    )
    
    # Add arrow pointing to user's value
    arrow_data = pd.DataFrame({
        'x': [int(round(user_value))],
        'y': [histogram_data[histogram_data['is_user_value']]['count'].sum() * 1.1],
        'label': ['Ta réponse ↓']
    })
    
    arrow = alt.Chart(arrow_data).mark_text(
        align='center',
        baseline='bottom',
        fontSize=14,
        fontWeight='bold',
        color='#E53E3E'
    ).encode(
        x='x:O',
        y='y:Q',
        text='label:N'
    )
    
    # Combine all elements
    chart = (bars + user_highlight + arrow).properties(
        width='container',
        height=350,
        title={
            "text": f"Distribution des réponses" + (" (ton groupe)" if not show_other_groups else " (tous les groupes)"),
            "fontSize": 16,
            "anchor": "start"
        }
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        domainWidth=1
    )
    
    return chart, user_percentile

def is_yes_no_question(df, question_col):
    """Check if a question is a yes/no type question."""
    unique_values = df[question_col].dropna().unique()
    yes_no_patterns = [
        ['oui', 'non'],
        ['yes', 'no'],
        ['Oui', 'Non'],
        ['OUI', 'NON']
    ]
    
    # Check if values match yes/no patterns
    values_lower = [str(v).lower().strip() for v in unique_values]
    for pattern in yes_no_patterns:
        if set(values_lower).issubset(set(pattern)):
            return True
    
    # Also check if it's binary with only 2 values
    return len(unique_values) == 2

def plot_pie_comparison(df, question_col, classifier_col, user_value, show_other_groups=True):
    """
    Crée des graphiques en camembert pour les questions oui/non.
    """
    # Get user's group
    user_group = user_data[classifier_col] if 'user_data' in globals() else None

    # Filter data based on show_other_groups option
    df_plot = df.copy()
    if not show_other_groups and user_group:
        df_plot = df_plot[df_plot[classifier_col] == user_group]

    # Get unique groups for creating multiple pie charts
    groups = sorted(df_plot[classifier_col].dropna().unique())
    
    # Create charts for each group
    charts = []
    
    for i, group in enumerate(groups):
        group_data = df_plot[df_plot[classifier_col] == group]
        value_counts = group_data[question_col].value_counts()
        
        # Create data for this group's pie chart
        pie_data = []
        for value, count in value_counts.items():
            pie_data.append({
                'response': str(value),
                'count': count,
                'percentage': (count / len(group_data) * 100),
                'is_user_response': value == user_value and group == user_group
            })
        
        pie_df = pd.DataFrame(pie_data)
        
        # Determine colors for yes/no
        response_colors = {}
        for response in pie_df['response'].unique():
            response_lower = response.lower().strip()
            if response_lower in ['oui', 'yes']:
                response_colors[response] = '#2ECC71'  # Green
            elif response_lower in ['non', 'no']:
                response_colors[response] = '#E74C3C'  # Red
            else:
                response_colors[response] = '#95A5A6'  # Gray for other
        
        # Create pie chart for this group
        base = alt.Chart(pie_df).mark_arc(
            innerRadius=40,
            stroke='white',
            strokeWidth=2
        ).encode(
            theta=alt.Theta('count:Q'),
            color=alt.Color('response:N',
                           scale=alt.Scale(
                               domain=list(response_colors.keys()),
                               range=list(response_colors.values())
                           ),
                           legend=None if i > 0 else alt.Legend(
                               orient='bottom',
                               title='Réponse'
                           )),
            opacity=alt.condition(
                alt.datum.is_user_response,
                alt.value(1.0),
                alt.value(0.7)
            ),
            tooltip=[
                alt.Tooltip('response:N', title='Réponse'),
                alt.Tooltip('count:Q', title='Nombre'),
                alt.Tooltip('percentage:Q', title='Pourcentage', format='.1f')
            ]
        ).properties(
            width=180,
            height=180,
            title={
                "text": f"{get_group_icon(group)} {group}",
                "color": get_group_color(group),
                "fontSize": 14,
                "fontWeight": "bold"
            }
        )
        
        # Add percentage labels
        labels = alt.Chart(pie_df).mark_text(
            radius=70,
            fontSize=12,
            fontWeight='bold',
            color='white'
        ).encode(
            theta=alt.Theta('count:Q'),
            text=alt.Text('percentage:Q', format='.0f')
        )
        
        # Add response labels
        response_labels = alt.Chart(pie_df).mark_text(
            radius=100,
            fontSize=11
        ).encode(
            theta=alt.Theta('count:Q'),
            text='response:N'
        )
        
        charts.append(base + labels + response_labels)
    
    # Combine charts horizontally
    if len(charts) == 1:
        final_chart = charts[0]
    elif len(charts) == 2:
        final_chart = alt.hconcat(*charts)
    else:
        # For 3 or more, arrange in rows
        final_chart = alt.vconcat(
            *[alt.hconcat(*charts[i:i+3]) for i in range(0, len(charts), 3)]
        )
    
    return final_chart.properties(
        title={
            "text": f"Répartition des réponses" + (" (ton groupe)" if not show_other_groups else " (tous les groupes)"),
            "fontSize": 16,
            "anchor": "start"
        }
    ).configure_view(
        strokeWidth=0
    )

def plot_categorical_comparison(df, question_col, classifier_col, user_value, show_other_groups=True):
    """
    Crée un graphique à barres amélioré pour les catégories.
    """
    # Prepare safe column names
    df_plot = df.copy()
    col_map = {col: (col.replace(':', '\\:') if isinstance(col, str) and ':' in col else col)
               for col in df_plot.columns}
    if any(col_map[c] != c for c in col_map):
        df_plot = df_plot.rename(columns=col_map)

    q_field = col_map.get(question_col, question_col)
    cls_field = col_map.get(classifier_col, classifier_col)

    # Get user's group
    user_group = df_plot[df_plot[col_map.get(classifier_col, classifier_col)] == user_data[classifier_col]].iloc[0][cls_field] if 'user_data' in globals() else None

    # Filter data based on show_other_groups option
    if not show_other_groups and user_group:
        df_plot = df_plot[df_plot[cls_field] == user_group]

    # Calculate percentage for each category
    grouped = df_plot.groupby([q_field, cls_field]).size().reset_index(name='count')
    total = grouped.groupby(q_field)['count'].transform('sum')
    grouped['percentage'] = (grouped['count'] / total * 100).round(1)
    
    # Mark user's response
    grouped['is_user_response'] = grouped[q_field] == user_value
    
    # Get color scale
    color_scale = get_color_scale(df_plot, cls_field)

    # Enhanced bar chart
    bars = alt.Chart(grouped).mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4
    ).encode(
        x=alt.X(f"{q_field}:N", 
                title=None,
                axis=alt.Axis(
                    labelAngle=-45 if len(grouped[q_field].unique()) > 3 else 0,
                    labelFontSize=12
                )),
        y=alt.Y('count:Q', 
                title="Nombre de réponses",
                stack='zero',
                axis=alt.Axis(
                    titleFontSize=14,
                    labelFontSize=12,
                    grid=True,
                    gridOpacity=0.3
                )),
        color=alt.Color(f"{cls_field}:N", 
                       title="Type de répondant",
                       scale=color_scale,
                       legend=alt.Legend(
                           orient='bottom',
                           titleFontSize=12,
                           labelFontSize=11
                       )),
        opacity=alt.condition(
            alt.datum.is_user_response,
            alt.value(1.0),
            alt.value(0.4)
        ),
        tooltip=[
            alt.Tooltip(q_field, type='nominal', title=question_col),
            alt.Tooltip(cls_field, type='nominal', title=classifier_col),
            alt.Tooltip('count:Q', title='Nombre'),
            alt.Tooltip('percentage:Q', title='Pourcentage', format='.1f')
        ]
    )
    
    # Highlight border for user's response
    user_bars = alt.Chart(grouped[grouped['is_user_response']]).mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
        stroke='#E53E3E',
        strokeWidth=3,
        fillOpacity=0
    ).encode(
        x=alt.X(f"{q_field}:N"),
        y=alt.Y('count:Q', stack='zero'),
        color=alt.Color(f"{cls_field}:N", scale=color_scale, legend=None)
    )
    
    # Add percentage labels on bars
    text = alt.Chart(grouped).mark_text(
        dy=-5,
        fontSize=11,
        fontWeight='bold'
    ).encode(
        x=alt.X(f"{q_field}:N"),
        y=alt.Y('count:Q', stack='zero'),
        text=alt.Text('percentage:Q', format='.0f'),
        color=alt.value('white'),
        opacity=alt.condition(
            alt.datum.is_user_response,
            alt.value(1.0),
            alt.value(0)
        )
    )
    
    final_chart = (bars + user_bars + text).properties(
        width='container',
        height=350,
        title={
            "text": f"Répartition des réponses" + (" (ton groupe)" if not show_other_groups else " (tous les groupes)"),
            "fontSize": 16,
            "anchor": "start"
        }
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        domainWidth=1
    )
    
    return final_chart

# --- MAIN APPLICATION ---

# Header with emoji and styling
st.markdown("# 🌙 Ton Bilan Sommeil")
st.markdown("### Découvre comment tu te situes par rapport aux autres participants")

# Load data
with st.spinner('Chargement des données...'):
    all_data = load_data(SHEET_URL)

if all_data.empty:
    st.stop()

# User identification section with improved styling
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("## 🔐 Retrouve tes résultats")

col1, col2 = st.columns([3, 1])
with col1:
    user_id = st.text_input(
        "Entre ton code secret:",
        placeholder="Tape ton code ici...",
        help="C'est le code que tu as créé lors du questionnaire"
    )

if not user_id:
    st.info("💡 Entre ton code secret ci-dessus pour voir tes résultats personnalisés.")
    st.stop()

# Filter user data
try:
    user_data_row = all_data[all_data[IDENTIFIER_COL].str.lower().str.strip() == user_id.lower().strip()]
except AttributeError:
    user_data_row = all_data[all_data[IDENTIFIER_COL] == user_id]

if user_data_row.empty:
    st.error(f"❌ Code non trouvé: '{user_id}'. Vérifie l'orthographe et réessaie.")
    st.stop()

user_data = user_data_row.iloc[0]
user_classifier = user_data[CLASSIFIER_COL]

# Success message with custom styling and group icon
group_icon = get_group_icon(user_classifier)
group_color = get_group_color(user_classifier)

st.markdown(f"""
<div class="metric-card" style="border-left: 4px solid {group_color};">
    <h3>✨ Bienvenue!</h3>
    <p>Nous avons trouvé tes réponses.</p>
    <p><strong>Tu fais partie du groupe:</strong> 
        <span style="color: {group_color}; font-size: 1.5em;">{group_icon} {user_classifier}</span>
    </p>
</div>
""", unsafe_allow_html=True)

# Results section
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("## 📊 Tes réponses en détail")

# Add toggle for showing all groups vs just user's group
col1, col2 = st.columns([2, 1])
with col1:
    show_all_groups = st.toggle(
        "Comparer avec tous les groupes",
        value=True,
        help="Active pour voir toutes les réponses, désactive pour voir seulement ton groupe"
    )

# Scale questions section
if SCALE_QUESTIONS:
    st.markdown("### 📈 Questions sur une échelle (1-10)")
    
    for i, q_col in enumerate(SCALE_QUESTIONS):
        # Try to find the question in the data with different encodings
        actual_col = None
        for col in all_data.columns:
            if any(word in col for word in q_col.split()) and len([word for word in q_col.split() if word in col]) > 3:
                actual_col = col
                break
        
        if actual_col is None:
            actual_col = q_col
            
        with st.expander(f"📌 {q_col}", expanded=(i==0)):
            try:
                user_answer = user_data[actual_col]
                if pd.isna(user_answer):
                    st.warning("Tu n'as pas répondu à cette question.")
                else:
                    chart, percentile = plot_numerical_comparison(
                        df=all_data,
                        question_col=actual_col,
                        classifier_col=CLASSIFIER_COL,
                        user_value=user_answer,
                        show_other_groups=show_all_groups
                    )
                    st.altair_chart(chart, use_container_width=True)
                    
                    # Add insight with group colors
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Ta réponse", f"{int(user_answer)}/10")
                    with col2:
                        st.metric("Position", f"{percentile:.0f}e percentile")
                    
                    # Color-coded feedback
                    group_color = get_group_color(user_classifier)
                    if percentile > 75:
                        st.markdown(f'<div style="background: {group_color}20; padding: 10px; border-radius: 8px; border-left: 4px solid {group_color};">👍 <strong>Excellent!</strong> Tu es dans le quart supérieur!</div>', unsafe_allow_html=True)
                    elif percentile < 25:
                        st.markdown(f'<div style="background: #FFF3CD; padding: 10px; border-radius: 8px; border-left: 4px solid #FFC107;">💭 <strong>Attention:</strong> Tu es dans le quart inférieur.</div>', unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"Erreur: {e}")

# Categorical questions section
if CATEGORY_QUESTIONS:
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📋 Questions à choix")
    
    for i, q_col in enumerate(CATEGORY_QUESTIONS):
        # Try to find the question in the data with different encodings
        actual_col = None
        for col in all_data.columns:
            if 'Scénario' in col and '22 h 30' in col:
                actual_col = col
                break
            elif q_col in col or col in q_col:
                actual_col = col
                break
        
        if actual_col is None:
            actual_col = q_col
        
        with st.expander(f"📌 {q_col}", expanded=(i==0)):
            try:
                user_answer = user_data[actual_col]
                if pd.isna(user_answer):
                    st.warning("Tu n'as pas répondu à cette question.")
                else:
                    # Check if it's a yes/no question
                    if is_yes_no_question(all_data, actual_col):
                        # Use pie charts for yes/no questions
                        chart = plot_pie_comparison(
                            df=all_data,
                            question_col=actual_col,
                            classifier_col=CLASSIFIER_COL,
                            user_value=user_answer,
                            show_other_groups=show_all_groups
                        )
                    else:
                        # Use bar charts for other categorical questions
                        chart = plot_categorical_comparison(
                            df=all_data,
                            question_col=actual_col,
                            classifier_col=CLASSIFIER_COL,
                            user_value=user_answer,
                            show_other_groups=show_all_groups
                        )
                    
                    st.altair_chart(chart, use_container_width=True)
                    
                    # Show user's answer prominently
                    group_icon = get_group_icon(user_classifier)
                    group_color = get_group_color(user_classifier)
                    st.markdown(f"""
                    <div style="background: {group_color}20; padding: 15px; border-radius: 8px; border-left: 4px solid {group_color};">
                        <span style="font-size: 1.5em;">{group_icon}</span>
                        <strong style="color: {group_color};">Ta réponse:</strong> {user_answer}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Calculate how many people gave the same answer
                    same_answer = all_data[all_data[actual_col] == user_answer].shape[0]
                    total = all_data[actual_col].notna().sum()
                    percentage = (same_answer / total * 100) if total > 0 else 0
                    
                    st.markdown(f"*{same_answer} personnes ({percentage:.0f}%) ont donné la même réponse*")
                    
            except Exception as e:
                st.error(f"Erreur: {e}")

# Summary statistics with group breakdown
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
with st.expander("📊 Statistiques globales"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Participants totaux", all_data.shape[0])
    with col2:
        st.metric("Groupes", all_data[CLASSIFIER_COL].nunique())
    with col3:
        st.metric("Questions", len(SCALE_QUESTIONS) + len(CATEGORY_QUESTIONS))
    
    # Group breakdown
    st.markdown("### Répartition par groupe:")
    group_counts = all_data[CLASSIFIER_COL].value_counts()
    for group, count in group_counts.items():
        icon = get_group_icon(group)
        color = get_group_color(group)
        percentage = (count / all_data.shape[0] * 100)
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 0.5rem 0;">
            <span style="color: {color}; font-size: 1.5em; margin-right: 0.5rem;">{icon}</span>
            <span style="flex: 1;"><strong>{group}:</strong> {count} participants ({percentage:.1f}%)</span>
        </div>
        """, unsafe_allow_html=True)

# Raw data (optional)
if st.checkbox("🔍 Voir les données brutes (anonymisées)"):
    st.dataframe(
        all_data.drop(columns=[IDENTIFIER_COL], errors='ignore'),
        use_container_width=True,
        height=400
    )

# Footer
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em; margin-top: 2rem;">
    <p>💡 Astuce: Cette page s'adapte automatiquement à ton écran!</p>
    <p>📱 Fonctionne parfaitement sur mobile</p>
</div>
""", unsafe_allow_html=True)