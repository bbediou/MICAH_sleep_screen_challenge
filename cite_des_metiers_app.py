# region imports
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
from collections import Counter
# Vérifier que wordcloud est disponible, sinon l'installer
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt

    wordcloud_available = True
except ImportError:
    st.error("📦 La bibliothèque 'wordcloud' n'est pas installée. Veuillez l'installer avec : `pip install wordcloud`")
    wordcloud_available = False
# endregion

# region Config
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

#endregion

# region Charger les données et afficher les noms des colonnes
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
# endregion

# region Afficher plus d'informations sur la structure des données
st.write("Informations sur les données :")
st.write(f"Nombre de lignes : {len(df)}")
st.write(f"Nombre de colonnes : {len(df.columns)}")
st.write("Colonnes :", df.columns.tolist())

# Afficher un aperçu des données
st.write("Aperçu des données :")
st.dataframe(df.head())
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

    #fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
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
        import re
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

#endregion

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

# region Graphique pour les préoccupations liées à l'IA
st.subheader("🤖 Préoccupations concernant l'Intelligence Artificielle")

ai_concern_column = 'Dans quelle mesure êtes-vous préoccupé par les IA ?'
age_category_column = 'Tu es :'  # Colonne qui distingue ados/adultes

if ai_concern_column in df.columns:

    # Afficher les statistiques générales
    ai_concerns = df[ai_concern_column].dropna()
    valid_responses = ai_concerns[(ai_concerns >= 1) & (ai_concerns <= 10)]

    if len(valid_responses) > 0:
        st.write("**📊 Statistiques générales :**")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Moyenne", f"{valid_responses.mean():.1f}/10")
        with col2:
            st.metric("Réponses", len(valid_responses))

        # Afficher la réponse du participant
        participant_ai_concern = None
        if valid_code and participant_data is not None:
            participant_ai_concern = participant_data[ai_concern_column]
            if pd.notna(participant_ai_concern) and 1 <= participant_ai_concern <= 10:
                st.info(f"🎯 **Ta réponse :** {int(participant_ai_concern)}/10")

                # Interpréter la réponse
                if participant_ai_concern <= 3:
                    interpretation = "Tu es peu préoccupé par l'IA 😌"
                elif participant_ai_concern <= 6:
                    interpretation = "Tu as un niveau modéré de préoccupation concernant l'IA 🤔"
                else:
                    interpretation = "Tu es assez préoccupé par l'IA 😰"

                st.write(f"**Interprétation :** {interpretation}")

        # Créer le graphique principal
        fig1 = create_numeric_scale_chart(
            df, ai_concern_column,
            "Distribution des niveaux de préoccupation concernant l'IA",
            participant_ai_concern
        )
        st.pyplot(fig1)

        # Ajouter la légende si un participant est mis en évidence
        if valid_code and participant_data is not None and pd.notna(participant_ai_concern):
            st.caption("🔴 **Barre avec bordure rouge** : Votre réponse")

        # Comparaison par groupe d'âge
        if age_category_column in df.columns:
            st.subheader("📈 Comparaison Adolescents vs Adultes")

            fig2 = create_age_category_comparison_chart(df, ai_concern_column, age_category_column,
                                                        "Comparaison des préoccupations IA : Ados vs Adultes")
            if fig2 is not None:
                st.pyplot(fig2)

                # Analyse comparative détaillée
                valid_comparison_data = df[
                    (df[ai_concern_column].between(1, 10)) &
                    (df[age_category_column].notna())
                    ].copy()

                valid_comparison_data['Groupe_Simple'] = valid_comparison_data[age_category_column].apply(
                    lambda x: "Adolescents" if pd.notna(x) and "ado" in str(x).lower() else
                    "Adultes" if pd.notna(x) and "adulte" in str(x).lower() else "Autre"
                )

                comparison_stats = \
                valid_comparison_data[valid_comparison_data['Groupe_Simple'].isin(['Adolescents', 'Adultes'])].groupby(
                    'Groupe_Simple')[ai_concern_column].agg(['mean', 'count', 'std']).round(2)

                if len(comparison_stats) > 0:
                    st.write("**🔍 Analyse comparative :**")
                    for group, stats in comparison_stats.iterrows():
                        st.write(
                            f"- **{group}** : Moyenne de {stats['mean']:.1f}/10 ± {stats['std']:.1f} ({int(stats['count'])} réponses)")

                    if len(comparison_stats) == 2:
                        diff = abs(
                            comparison_stats.loc['Adultes', 'mean'] - comparison_stats.loc['Adolescents', 'mean'])
                        if diff > 1:
                            st.write(f"📊 **Différence notable** : {diff:.1f} points entre adolescents et adultes")
                        else:
                            st.write("📊 **Différence faible** entre adolescents et adultes")

                        # Déterminer qui est plus préoccupé
                        if 'Adultes' in comparison_stats.index and 'Adolescents' in comparison_stats.index:
                            adult_mean = comparison_stats.loc['Adultes', 'mean']
                            teen_mean = comparison_stats.loc['Adolescents', 'mean']

                            if adult_mean > teen_mean:
                                st.write(
                                    f"👨‍👩‍👧‍👦 Les **adultes** sont plus préoccupés que les **adolescents** ({adult_mean:.1f} vs {teen_mean:.1f})")
                            elif teen_mean > adult_mean:
                                st.write(
                                    f"🧑‍🎓 Les **adolescents** sont plus préoccupés que les **adultes** ({teen_mean:.1f} vs {adult_mean:.1f})")
                            else:
                                st.write("⚖️ **Niveau de préoccupation similaire** entre les deux groupes")

            else:
                st.warning("Données insuffisantes pour la comparaison par groupe d'âge")
        else:
            st.warning(f"Colonne de catégorie d'âge '{age_category_column}' non trouvée pour la comparaison")
            st.write("Colonnes disponibles :")
            st.write(
                [col for col in df.columns if 'tu es' in col.lower() or 'âge' in col.lower() or 'age' in col.lower()])

    else:
        st.warning("Aucune réponse valide trouvée pour cette question")

else:
    st.error(f"Colonne '{ai_concern_column}' non trouvée dans les données")
    st.write("Colonnes disponibles contenant 'IA' ou similaire :")
    ai_columns = [col for col in df.columns if
                  'IA' in col.upper() or 'INTELLIGENCE' in col.upper() or 'PRÉOCCUP' in col.upper()]
    if ai_columns:
        st.write(ai_columns)
    else:
        st.write("Aucune colonne trouvée. Voici toutes les colonnes :")
        st.write(df.columns.tolist())

# endregion

# region Word Cloud des fonctionnalités IA souhaitées
st.subheader("☁️ Fonctionnalités IA souhaitées - Nuages de mots")

ai_features_column = 'Quelle fonctionnalité aimeriez-vous implémenter dans l\'IA ?'

if wordcloud_available and ai_features_column in df.columns and age_category_column in df.columns:

    # Vérifier s'il y a des données
    valid_responses = df[(df[ai_features_column].notna()) & (df[age_category_column].notna())]

    if len(valid_responses) > 0:
        # Compter les réponses par groupe
        def simplify_category(category):
            if pd.isna(category):
                return "Non spécifié"
            elif "ado" in category.lower():
                return "Adolescents"
            elif "adulte" in category.lower():
                return "Adultes"
            else:
                return category


        valid_responses_copy = valid_responses.copy()
        valid_responses_copy['Groupe_Simple'] = valid_responses_copy[age_category_column].apply(simplify_category)

        group_counts = valid_responses_copy['Groupe_Simple'].value_counts()
        adolescents_count = group_counts.get('Adolescents', 0)
        adultes_count = group_counts.get('Adultes', 0)

        # Afficher les statistiques
        st.write("**📊 Statistiques des réponses :**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🧑‍🎓 Adolescents", adolescents_count)
        with col2:
            st.metric("👨‍👩‍👧‍👦 Adultes", adultes_count)
        with col3:
            st.metric("📝 Total", len(valid_responses))

        # Créer les word clouds
        wc_adolescents, wc_adultes = create_wordcloud_comparison(df, ai_features_column, age_category_column)

        # Afficher les word clouds
        fig = plot_wordclouds(wc_adolescents, wc_adultes, adolescents_count, adultes_count)
        if fig is not None:
            st.pyplot(fig)

            # Ajouter des explications
            st.write("**💡 Comment lire ces nuages de mots :**")
            st.write("- Plus un mot est **grand**, plus il apparaît fréquemment dans les réponses")
            st.write("- Les couleurs **orange** représentent les réponses des adolescents")
            st.write("- Les couleurs **bleues** représentent les réponses des adultes")

            # Afficher quelques réponses exemples si le participant a un code valide
            if valid_code and participant_data is not None:
                participant_response = participant_data[ai_features_column]
                if pd.notna(participant_response):
                    st.info(f"🎯 **Ta réponse :** {participant_response}")

        # Optionnel: Afficher les réponses les plus fréquentes
        st.subheader("🔤 Mots les plus fréquents")

        # Analyser les mots les plus fréquents pour chaque groupe
        from collections import Counter
        import re


        def get_top_words(text_series, top_n=10):
            if len(text_series) == 0:
                return []

            # Combiner tout le texte
            all_text = ' '.join(text_series.astype(str).str.lower())

            # Extraire les mots (supprimer la ponctuation)
            words = re.findall(r'\b\w+\b', all_text)

            # Filtrer les mots trop courts ou communs
            stop_words = {'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'de', 'du', 'dans', 'avec', 'pour', 'sur',
                          'par', 'que', 'qui', 'ce', 'cette', 'ces', 'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils',
                          'elles', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses', 'à', 'au', 'aux'}
            filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]

            # Compter les occurrences
            word_counts = Counter(filtered_words)
            return word_counts.most_common(top_n)


        adolescents_data = valid_responses_copy[valid_responses_copy['Groupe_Simple'] == 'Adolescents'][
            ai_features_column]
        adultes_data = valid_responses_copy[valid_responses_copy['Groupe_Simple'] == 'Adultes'][ai_features_column]

        col1, col2 = st.columns(2)

        with col1:
            if len(adolescents_data) > 0:
                st.write("**🧑‍🎓 Top mots - Adolescents :**")
                top_words_ados = get_top_words(adolescents_data, 8)
                for i, (word, count) in enumerate(top_words_ados, 1):
                    st.write(f"{i}. **{word}** ({count} fois)")

        with col2:
            if len(adultes_data) > 0:
                st.write("**👨‍👩‍👧‍👦 Top mots - Adultes :**")
                top_words_adultes = get_top_words(adultes_data, 8)
                for i, (word, count) in enumerate(top_words_adultes, 1):
                    st.write(f"{i}. **{word}** ({count} fois)")

    else:
        st.warning("Aucune réponse valide trouvée pour cette question")

elif not wordcloud_available:
    st.info("💡 Pour installer wordcloud : `pip install wordcloud`")

else:
    st.error(f"Colonnes requises non trouvées :")
    if ai_features_column not in df.columns:
        st.write(f"- '{ai_features_column}' non trouvée")
    if age_category_column not in df.columns:
        st.write(f"- '{age_category_column}' non trouvée")

    st.write("Colonnes disponibles :")
    st.write(
        [col for col in df.columns if 'fonctionnalité' in col.lower() or 'implémenter' in col.lower() or 'IA' in col])

# endregion

# region Graphique en donut des préférences de campagnes de prévention
st.subheader("🍩 Préférences pour les campagnes de prévention IA")
prevention_column = 'Les campagnes de prévention sont souvent austères, parmi les éléments suivants, lesquels t’aideraient à mieux comprendre les informations sur la bonne utilisation et la sécurité des IA? '

if prevention_column in df.columns and age_category_column in df.columns:
    # Traiter les données
    valid_responses = df[(df[prevention_column].notna()) & (df[age_category_column].notna())]

    if len(valid_responses) > 0:
        # Obtenir les comptes pour chaque groupe
        adolescents_counts, adultes_counts = create_donut_comparison(df, prevention_column, age_category_column)

        # Afficher les statistiques générales
        total_adolescents = sum(adolescents_counts.values()) if adolescents_counts else 0
        total_adultes = sum(adultes_counts.values()) if adultes_counts else 0

        st.write("**📊 Statistiques des réponses :**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🧑‍🎓 Réponses Adolescents", total_adolescents)
        with col2:
            st.metric("👨‍👩‍👧‍👦 Réponses Adultes", total_adultes)
        with col3:
            st.metric("📝 Total", total_adolescents + total_adultes)

        # Créer et afficher les graphiques
        fig = plot_donut_charts(adolescents_counts, adultes_counts)
        if fig is not None:
            st.pyplot(fig)

            # Ajouter la réponse du participant si disponible
            if valid_code and participant_data is not None:
                participant_response = participant_data[prevention_column]
                if pd.notna(participant_response):
                    st.info(f"🎯 **Ta réponse :** {participant_response}")

            # Afficher les détails des réponses les plus populaires
            st.subheader("🏆 Réponses les plus populaires")

            col1, col2 = st.columns(2)

            with col1:
                if adolescents_counts:
                    st.write("**🧑‍🎓 Top 3- Adolescents :**")
                    for i, (answer, count) in enumerate(adolescents_counts.most_common(3), 1):
                        percentage = (count / total_adolescents) * 100
                        st.write(f"{i}. **{answer}** - {count} fois ({percentage:.1f}%)")

            with col2:
                if adultes_counts:
                    st.write("**👨‍👩‍👧‍👦 Top 3 - Adultes :**")
                    for i, (answer, count) in enumerate(adultes_counts.most_common(3), 1):
                        percentage = (count / total_adultes) * 100
                        st.write(f"{i}. **{answer}** - {count} fois ({percentage:.1f}%)")

            # Analyse comparative
            if adolescents_counts and adultes_counts:
                st.subheader("🔍 Analyse comparative")

                # Trouver les réponses communes
                common_answers = set(adolescents_counts.keys()) & set(adultes_counts.keys())
                if common_answers:
                    st.write("**🤝 Réponses communes aux deux groupes :**")
                    for answer in common_answers:
                        ado_count = adolescents_counts[answer]
                        adult_count = adultes_counts[answer]
                        ado_pct = (ado_count / total_adolescents) * 100
                        adult_pct = (adult_count / total_adultes) * 100

                        if abs(ado_pct - adult_pct) < 5:
                            trend = "📊 Similaire"
                        elif ado_pct > adult_pct:
                            trend = "🧑‍🎓 Plus populaire chez les ados"
                        else:
                            trend = "👨‍👩‍👧‍👦 Plus populaire chez les adultes"

                        st.write(f"- **{answer}** - {trend}")
                        st.write(f"  - Ados: {ado_count} ({ado_pct:.1f}%) | Adultes: {adult_count} ({adult_pct:.1f}%)")

                # Réponses uniques à chaque groupe
                ado_only = set(adolescents_counts.keys()) - set(adultes_counts.keys())
                adult_only = set(adultes_counts.keys()) - set(adolescents_counts.keys())

                if ado_only:
                    st.write("**🧑‍🎓 Réponses spécifiques aux adolescents :**")
                    for answer in ado_only:
                        count = adolescents_counts[answer]
                        pct = (count / total_adolescents) * 100
                        st.write(f"- **{answer}** ({count} - {pct:.1f}%)")

                if adult_only:
                    st.write("**👨‍👩‍👧‍👦 Réponses spécifiques aux adultes :**")
                    for answer in adult_only:
                        count = adultes_counts[answer]
                        pct = (count / total_adultes) * 100
                        st.write(f"- **{answer}** ({count} - {pct:.1f}%)")

        else:
            st.warning("Impossible de créer les graphiques - données insuffisantes")

    else:
        st.warning("Aucune réponse valide trouvée pour cette question")

else:
    st.error("Colonnes requises non trouvées :")
    if prevention_column not in df.columns:
        st.write(f"- Question sur les campagnes de prévention non trouvée")
        # Chercher des colonnes similaires
        similar_cols = [col for col in df.columns if
                        'campagne' in col.lower() or 'prévention' in col.lower() or 'austère' in col.lower()]
        if similar_cols:
            st.write("Colonnes similaires trouvées :")
            st.write(similar_cols)

    if age_category_column not in df.columns:
        st.write(f"- Colonne de catégorie d'âge '{age_category_column}' non trouvée")

# endregion