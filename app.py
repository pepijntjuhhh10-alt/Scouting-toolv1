import streamlit as st
import pandas as pd

st.set_page_config(page_title="Player Fit Model", layout="wide")

st.title("⚽ Player Fit Model")
st.caption("Per-90 scoutingmodel: beste rol, Feyenoord-fit en top 7 league-fit")

LEAGUES = {
    "Premier League": 1.00,
    "La Liga": 0.97,
    "Bundesliga": 0.96,
    "Serie A": 0.95,
    "Ligue 1": 0.92,
    "Eredivisie": 0.86,
    "Primeira Liga": 0.85,
}

LEAGUE_DEMANDS = {
    "Premier League": {"physical": 1.15, "defending": 1.10, "duels": 1.15, "tempo": 1.15, "technical": 1.00, "attacking": 1.00},
    "La Liga": {"physical": 0.95, "defending": 1.00, "duels": 0.95, "tempo": 1.00, "technical": 1.15, "attacking": 1.05},
    "Bundesliga": {"physical": 1.10, "defending": 1.05, "duels": 1.10, "tempo": 1.15, "technical": 1.00, "attacking": 1.05},
    "Serie A": {"physical": 1.00, "defending": 1.15, "duels": 1.05, "tempo": 0.95, "technical": 1.05, "attacking": 1.00},
    "Ligue 1": {"physical": 1.15, "defending": 1.00, "duels": 1.10, "tempo": 1.10, "technical": 0.95, "attacking": 1.00},
    "Eredivisie": {"physical": 0.90, "defending": 0.90, "duels": 0.90, "tempo": 0.95, "technical": 1.05, "attacking": 1.05},
    "Primeira Liga": {"physical": 1.00, "defending": 1.00, "duels": 1.00, "tempo": 1.00, "technical": 1.10, "attacking": 1.05},
}

METRIC_RANGES = {
    "xg": (0.00, 0.20, 0.60),
    "xa": (0.00, 0.12, 0.35),
    "goals": (0.00, 0.20, 0.70),
    "shots": (0.20, 1.80, 4.00),
    "key_passes": (0.20, 1.20, 3.00),
    "touches_att_pen": (0.50, 3.50, 8.00),

    "progressive_passes": (1.00, 4.00, 8.00),
    "passes_into_final_third": (1.00, 3.50, 7.00),
    "passes_completed_pct": (65.0, 80.0, 92.0),

    "carries": (15.0, 35.0, 60.0),
    "progressive_carries": (0.50, 2.50, 6.00),
    "successful_take_ons": (0.20, 1.30, 3.50),
    "crosses": (0.20, 2.50, 6.00),

    "tackles": (0.50, 2.00, 4.00),
    "interceptions": (0.30, 1.30, 3.00),
    "blocks": (0.40, 1.50, 3.20),
    "duels_won_pct": (35.0, 52.0, 70.0),
    "aerials_won_pct": (35.0, 55.0, 75.0),

    "miscontrols": (3.00, 1.50, 0.30),
    "dispossessed": (3.00, 1.50, 0.30),

    "save_pct": (55.0, 70.0, 82.0),
    "psxg_g_minus_ga": (-0.30, 0.00, 0.30),
    "passes_attempted": (15.0, 30.0, 50.0),
    "launch_pct": (70.0, 45.0, 20.0),
    "def_actions_outside_box": (0.20, 0.80, 1.80),
    "crosses_stopped": (3.0, 7.0, 12.0),
}

ROLES = {
    "Goalkeeper": {
        "Sweeper Keeper": {
            "save_pct": 0.30, "psxg_g_minus_ga": 0.25, "passes_attempted": 0.15,
            "launch_pct": 0.10, "def_actions_outside_box": 0.20, "crosses_stopped": 0.10,
        },
        "Shot Stopper": {
            "save_pct": 0.40, "psxg_g_minus_ga": 0.35, "crosses_stopped": 0.15,
            "passes_attempted": 0.05, "def_actions_outside_box": 0.05,
        },
    },

    "Fullback": {
        "Defensive Fullback": {
            "tackles": 0.22, "interceptions": 0.20, "blocks": 0.16, "duels_won_pct": 0.18,
            "progressive_passes": 0.10, "progressive_carries": 0.06, "crosses": 0.04,
            "miscontrols": 0.04,
        },
        "Attacking Fullback": {
            "progressive_carries": 0.22, "progressive_passes": 0.16, "crosses": 0.18,
            "key_passes": 0.14, "touches_att_pen": 0.10, "successful_take_ons": 0.10,
            "tackles": 0.06, "interceptions": 0.04,
        },
        "Inverted Fullback": {
            "passes_completed_pct": 0.18, "progressive_passes": 0.22, "passes_into_final_third": 0.18,
            "carries": 0.12, "progressive_carries": 0.12, "tackles": 0.08,
            "interceptions": 0.08, "miscontrols": 0.02,
        },
        "Wingback": {
            "progressive_carries": 0.22, "crosses": 0.20, "touches_att_pen": 0.14,
            "successful_take_ons": 0.12, "key_passes": 0.12, "tackles": 0.08,
            "duels_won_pct": 0.08, "interceptions": 0.04,
        },
    },

    "Centre Back": {
        "Ball Playing CB": {
            "progressive_passes": 0.25, "passes_into_final_third": 0.20, "passes_completed_pct": 0.15,
            "interceptions": 0.12, "aerials_won_pct": 0.12, "tackles": 0.08, "blocks": 0.08,
        },
        "Stopper CB": {
            "tackles": 0.20, "interceptions": 0.20, "blocks": 0.18, "aerials_won_pct": 0.20,
            "duels_won_pct": 0.14, "progressive_passes": 0.08,
        },
        "Cover CB": {
            "interceptions": 0.24, "progressive_carries": 0.14, "passes_completed_pct": 0.16,
            "tackles": 0.16, "blocks": 0.12, "progressive_passes": 0.12, "aerials_won_pct": 0.06,
        },
    },

    "Midfielder": {
        "Defensive Midfielder": {
            "tackles": 0.20, "interceptions": 0.20, "blocks": 0.10, "duels_won_pct": 0.15,
            "progressive_passes": 0.15, "passes_completed_pct": 0.12,
            "miscontrols": 0.04, "dispossessed": 0.04,
        },
        "Deep Playmaker": {
            "progressive_passes": 0.26, "passes_into_final_third": 0.22, "passes_completed_pct": 0.18,
            "key_passes": 0.10, "tackles": 0.10, "interceptions": 0.10, "miscontrols": 0.04,
        },
        "Box to Box": {
            "progressive_carries": 0.18, "progressive_passes": 0.16, "tackles": 0.14,
            "interceptions": 0.12, "touches_att_pen": 0.10, "xg": 0.10,
            "xa": 0.10, "duels_won_pct": 0.10,
        },
        "Attacking Midfielder": {
            "xa": 0.20, "key_passes": 0.20, "progressive_passes": 0.14,
            "progressive_carries": 0.14, "successful_take_ons": 0.12,
            "xg": 0.10, "touches_att_pen": 0.10,
        },
    },

    "Winger": {
        "Touchline Winger": {
            "successful_take_ons": 0.22, "progressive_carries": 0.22, "crosses": 0.16,
            "key_passes": 0.14, "xa": 0.12, "touches_att_pen": 0.08,
            "dispossessed": 0.06,
        },
        "Inside Forward": {
            "xg": 0.22, "shots": 0.16, "touches_att_pen": 0.16,
            "successful_take_ons": 0.16, "progressive_carries": 0.14,
            "xa": 0.10, "dispossessed": 0.06,
        },
        "Creative Winger": {
            "xa": 0.22, "key_passes": 0.22, "progressive_passes": 0.14,
            "progressive_carries": 0.14, "successful_take_ons": 0.12,
            "crosses": 0.10, "dispossessed": 0.06,
        },
        "Pressing Winger": {
            "tackles": 0.16, "interceptions": 0.14, "successful_take_ons": 0.14,
            "progressive_carries": 0.14, "xg": 0.12, "xa": 0.10,
            "duels_won_pct": 0.12, "touches_att_pen": 0.08,
        },
    },

    "Striker": {
        "Poacher": {
            "xg": 0.32, "shots": 0.22, "touches_att_pen": 0.20, "goals": 0.18,
            "xa": 0.04, "key_passes": 0.04,
        },
        "Complete Striker": {
            "xg": 0.20, "shots": 0.14, "touches_att_pen": 0.14, "xa": 0.12,
            "key_passes": 0.10, "progressive_carries": 0.10,
            "duels_won_pct": 0.12, "successful_take_ons": 0.08,
        },
        "Pressing Striker": {
            "tackles": 0.14, "interceptions": 0.10, "duels_won_pct": 0.16,
            "xg": 0.20, "shots": 0.14, "touches_att_pen": 0.14,
            "progressive_carries": 0.06, "key_passes": 0.06,
        },
        "Link-up Striker": {
            "xa": 0.18, "key_passes": 0.16, "passes_completed_pct": 0.14,
            "progressive_passes": 0.12, "duels_won_pct": 0.12,
            "touches_att_pen": 0.12, "xg": 0.10, "shots": 0.06,
        },
    },
}

FEYENOORD_WEIGHTS = {
    "technical": 0.22,
    "attacking": 0.22,
    "tempo": 0.18,
    "defending": 0.16,
    "physical": 0.14,
    "duels": 0.08,
}

ATTRIBUTE_MAP = {
    "technical": ["passes_completed_pct", "progressive_passes", "passes_into_final_third", "key_passes", "xa"],
    "attacking": ["xg", "goals", "shots", "xa", "touches_att_pen", "key_passes", "crosses"],
    "tempo": ["progressive_carries", "progressive_passes", "successful_take_ons", "carries"],
    "defending": ["tackles", "interceptions", "blocks"],
    "physical": ["duels_won_pct", "aerials_won_pct", "successful_take_ons", "progressive_carries"],
    "duels": ["duels_won_pct", "aerials_won_pct", "tackles"],
}

ALL_METRICS = sorted(
    set(
        metric
        for role_group in ROLES.values()
        for role in role_group.values()
        for metric in role.keys()
    )
)

def clamp(value, low=0, high=100):
    return max(low, min(high, value))

def per90_to_score(metric, value):
    low, avg, elite = METRIC_RANGES.get(metric, (0, 50, 100))

    if elite > low:
        if value <= low:
            return 0
        if value >= elite:
            return 100
        if value <= avg:
            return 50 * (value - low) / (avg - low)
        return 50 + 50 * (value - avg) / (elite - avg)

    # lager = beter
    if value >= low:
        return 0
    if value <= elite:
        return 100
    if value >= avg:
        return 50 * (low - value) / (low - avg)
    return 50 + 50 * (avg - value) / (avg - elite)

def weighted_score(values, weights):
    score = 0
    total_weight = 0

    for metric, weight in weights.items():
        raw_value = values.get(metric, 0)
        metric_score = per90_to_score(metric, raw_value)

        score += metric_score * weight
        total_weight += abs(weight)

    if total_weight == 0:
        return 50

    return clamp(score / total_weight)

def attribute_score(values, attribute):
    metrics = ATTRIBUTE_MAP.get(attribute, [])
    scores = [per90_to_score(m, values.get(m, 0)) for m in metrics]

    if not scores:
        return 50

    return clamp(sum(scores) / len(scores))

def calculate_feyenoord_fit(values):
    score = 0

    for attribute, weight in FEYENOORD_WEIGHTS.items():
        score += attribute_score(values, attribute) * weight

    return clamp(score)

def calculate_league_fit(values, league):
    demands = LEAGUE_DEMANDS[league]
    score = 0
    total = 0

    for attribute, demand in demands.items():
        attr_score = attribute_score(values, attribute)
        score += attr_score * demand
        total += demand

    return clamp(score / total)

def calculate_best_role(position, values):
    role_scores = {}

    for role, weights in ROLES[position].items():
        role_scores[role] = weighted_score(values, weights)

    best_role = max(role_scores, key=role_scores.get)
    best_score = role_scores[best_role]

    return best_role, best_score, role_scores

def label(score):
    if score >= 85:
        return "ELITE"
    if score >= 78:
        return "ZEER GOED"
    if score >= 70:
        return "INTERESSANT"
    if score >= 62:
        return "MONITOREN"
    return "NIET DOEN"

def advice_color(score):
    if score >= 78:
        return "🟢"
    if score >= 70:
        return "🟡"
    if score >= 62:
        return "🟠"
    return "🔴"

st.sidebar.header("Spelergegevens")

player_name = st.sidebar.text_input("Naam speler", "Flávio Nazinho")
position = st.sidebar.selectbox("Positie", list(ROLES.keys()))
current_league = st.sidebar.selectbox("Huidige competitie", list(LEAGUES.keys()), index=5)
minutes = st.sidebar.number_input("Minuten gespeeld", min_value=0, max_value=5000, value=1800, step=100)
age = st.sidebar.number_input("Leeftijd", min_value=15, max_value=45, value=22)

st.sidebar.markdown("---")
st.sidebar.header("Per 90 data")
st.sidebar.caption("Vul FBref per-90 data in. Percentages vul je als percentage in, bijvoorbeeld 82.5.")

DEFAULT_VALUES = {
    "xg": 0.20,
    "xa": 0.12,
    "goals": 0.20,
    "shots": 1.80,
    "key_passes": 1.20,
    "touches_att_pen": 3.50,
    "progressive_passes": 4.00,
    "passes_into_final_third": 3.50,
    "passes_completed_pct": 80.0,
    "carries": 35.0,
    "progressive_carries": 2.50,
    "successful_take_ons": 1.30,
    "crosses": 2.50,
    "tackles": 2.00,
    "interceptions": 1.30,
    "blocks": 1.50,
    "duels_won_pct": 52.0,
    "aerials_won_pct": 55.0,
    "miscontrols": 1.50,
    "dispossessed": 1.50,
    "save_pct": 70.0,
    "psxg_g_minus_ga": 0.00,
    "passes_attempted": 30.0,
    "launch_pct": 45.0,
    "def_actions_outside_box": 0.80,
    "crosses_stopped": 7.0,
}

values = {}

for metric in ALL_METRICS:
    values[metric] = st.sidebar.number_input(
        metric,
        min_value=-5.0,
        max_value=100.0,
        value=float(DEFAULT_VALUES.get(metric, 1.0)),
        step=0.1,
    )

best_role, best_role_score, role_scores = calculate_best_role(position, values)
feyenoord_fit = calculate_feyenoord_fit(values)

league_fits = {
    league: calculate_league_fit(values, league)
    for league in LEAGUES.keys()
}

current_factor = LEAGUES[current_league]

if minutes < 900:
    minutes_multiplier = 0.75
elif minutes < 1500:
    minutes_multiplier = 0.90
else:
    minutes_multiplier = 1.00

if age <= 21:
    age_bonus = 4
elif age <= 24:
    age_bonus = 2
elif age <= 28:
    age_bonus = 0
elif age <= 32:
    age_bonus = -4
else:
    age_bonus = -10

adjusted_score = clamp((best_role_score * current_factor * minutes_multiplier) + age_bonus)

transfer_rating = clamp(
    (adjusted_score * 0.50)
    + (feyenoord_fit * 0.30)
    + (max(league_fits.values()) * 0.20)
)

st.subheader(f"Resultaten voor {player_name}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Beste rol", best_role)

with col2:
    st.metric("Rolscore", round(best_role_score, 1))

with col3:
    st.metric("Feyenoord Fit", round(feyenoord_fit, 1))

with col4:
    st.metric("Transfer Rating", round(transfer_rating, 1))

st.markdown("### Advies")
st.info(
    f"{advice_color(transfer_rating)} **{label(transfer_rating)}** — "
    f"Beste rol: **{best_role}** | Feyenoord Fit: **{round(feyenoord_fit, 1)}**"
)

st.markdown("### Beste rol van de speler")

role_df = pd.DataFrame(
    [{"Rol": role, "Score": round(score, 1), "Advies": label(score)} for role, score in role_scores.items()]
).sort_values("Score", ascending=False)

st.dataframe(role_df, use_container_width=True)

st.markdown("### Top 7 League Fit")

league_df = pd.DataFrame(
    [
        {
            "Competitie": league,
            "League Fit": round(score, 1),
            "Niveau-factor": LEAGUES[league],
            "Advies": label(score),
        }
        for league, score in league_fits.items()
    ]
).sort_values("League Fit", ascending=False)

st.dataframe(league_df, use_container_width=True)

best_league = max(league_fits, key=league_fits.get)

st.success(
    f"Beste competitie-fit: **{best_league}** "
    f"met score **{round(league_fits[best_league], 1)}**."
)

st.markdown("### Interpretatie")

st.write(
    f"""
**{player_name}** wordt door het model het best gezien als **{best_role}**.

- **Rolscore:** {round(best_role_score, 1)}
- **Aangepaste score:** {round(adjusted_score, 1)}
- **Feyenoord Fit:** {round(feyenoord_fit, 1)}
- **Transfer Rating:** {round(transfer_rating, 1)}
- **Beste competitie-fit:** {best_league}

Let op: vul per-90 data in. Het model zet die automatisch om naar een 0-100 score.
"""
)
