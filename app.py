
import re
import time
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Next Step Model Pro", layout="wide")

st.title("⚽ Next Step Model Pro")
st.caption("FBref auto-import + beste rol + Feyenoord Fit + Top 7 League Fit")

# =========================================================
# LEGAL / SAFE SCRAPING SETTINGS
# =========================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (personal scouting model; contact: personal-use)"
}

# =========================================================
# LEAGUES
# =========================================================

LEAGUES = {
    "Premier League": 1.00,
    "La Liga": 0.97,
    "Bundesliga": 0.96,
    "Serie A": 0.95,
    "Ligue 1": 0.92,
    "Eredivisie": 0.86,
    "Primeira Liga": 0.85,
    "Belgian Pro League": 0.82,
    "Austrian Bundesliga": 0.78,
    "Czech First League": 0.76,
}

TOP7_LEAGUES = [
    "Premier League",
    "La Liga",
    "Bundesliga",
    "Serie A",
    "Ligue 1",
    "Eredivisie",
    "Primeira Liga",
]

# =========================================================
# METRIC RANGES
# low, average, elite
# For negative metrics: low = bad/high number, elite = good/low number
# =========================================================

METRIC_RANGES = {
    # Attacking / creation
    "xg_p90": (0.00, 0.20, 0.60),
    "xa_p90": (0.00, 0.12, 0.35),
    "goals_p90": (0.00, 0.20, 0.70),
    "assists_p90": (0.00, 0.12, 0.35),
    "shots_p90": (0.20, 1.80, 4.00),
    "key_passes_p90": (0.20, 1.20, 3.00),
    "shot_creating_actions_p90": (1.00, 3.20, 6.50),
    "touches_box_p90": (0.50, 3.50, 8.00),

    # Passing / progression
    "passes_attempted_p90": (20.0, 45.0, 80.0),
    "passes_completed_pct": (65.0, 80.0, 92.0),
    "prog_passes_p90": (1.00, 4.00, 8.00),
    "passes_final_third_p90": (1.00, 3.50, 7.00),
    "passes_penalty_area_p90": (0.20, 1.20, 3.50),
    "accurate_long_balls_p90": (0.30, 2.00, 5.00),

    # Carrying / dribbling
    "carries_p90": (15.0, 35.0, 60.0),
    "prog_carries_p90": (0.50, 2.50, 6.00),
    "take_ons_attempted_p90": (0.30, 2.00, 5.00),
    "take_ons_won_p90": (0.20, 1.30, 3.50),
    "dribble_success_pct": (35.0, 52.0, 70.0),

    # Wide play
    "crosses_p90": (0.20, 2.50, 6.00),

    # Defending
    "tackles_p90": (0.50, 2.00, 4.00),
    "tackles_won_p90": (0.30, 1.20, 3.00),
    "interceptions_p90": (0.30, 1.30, 3.00),
    "blocks_p90": (0.40, 1.50, 3.20),
    "clearances_p90": (0.50, 2.50, 6.00),
    "ball_recoveries_p90": (2.00, 5.00, 9.00),

    # Duels
    "duels_won_pct": (35.0, 52.0, 70.0),
    "aerials_won_pct": (35.0, 55.0, 75.0),
    "aerials_won_p90": (0.20, 1.50, 4.00),

    # Negative / security
    "miscontrols_p90": (3.00, 1.50, 0.30),
    "dispossessed_p90": (3.00, 1.50, 0.30),

    # Ratings / fallback
    "fotmob_rating": (6.30, 7.00, 7.70),
    "sofascore_rating": (6.40, 7.00, 7.70),
}

DEFAULT_VALUES = {
    metric: avg for metric, (_, avg, _) in METRIC_RANGES.items()
}

# =========================================================
# ROLE WEIGHTS
# =========================================================

ROLES = {
    "Keeper": {
        "Shot Stopper": {
            "fotmob_rating": 0.35,
            "sofascore_rating": 0.35,
            "passes_completed_pct": 0.10,
            "accurate_long_balls_p90": 0.10,
            "ball_recoveries_p90": 0.10,
        },
        "Sweeper Keeper": {
            "passes_completed_pct": 0.25,
            "accurate_long_balls_p90": 0.20,
            "passes_attempted_p90": 0.15,
            "ball_recoveries_p90": 0.15,
            "fotmob_rating": 0.15,
            "sofascore_rating": 0.10,
        },
    },
    "Back": {
        "Defensive Fullback": {
            "tackles_p90": 0.22,
            "interceptions_p90": 0.20,
            "blocks_p90": 0.14,
            "duels_won_pct": 0.16,
            "aerials_won_pct": 0.08,
            "prog_passes_p90": 0.08,
            "miscontrols_p90": 0.06,
            "dispossessed_p90": 0.06,
        },
        "Attacking Fullback": {
            "prog_carries_p90": 0.18,
            "prog_passes_p90": 0.14,
            "crosses_p90": 0.16,
            "key_passes_p90": 0.12,
            "xa_p90": 0.10,
            "touches_box_p90": 0.10,
            "take_ons_won_p90": 0.10,
            "tackles_p90": 0.06,
            "interceptions_p90": 0.04,
        },
        "Inverted Fullback": {
            "passes_completed_pct": 0.20,
            "prog_passes_p90": 0.22,
            "passes_final_third_p90": 0.16,
            "carries_p90": 0.10,
            "prog_carries_p90": 0.10,
            "interceptions_p90": 0.10,
            "tackles_p90": 0.08,
            "miscontrols_p90": 0.04,
        },
        "Wingback": {
            "prog_carries_p90": 0.20,
            "crosses_p90": 0.18,
            "touches_box_p90": 0.14,
            "take_ons_won_p90": 0.12,
            "key_passes_p90": 0.12,
            "xa_p90": 0.08,
            "tackles_p90": 0.08,
            "duels_won_pct": 0.08,
        },
    },
    "Centrale verdediger": {
        "Ball Playing CB": {
            "prog_passes_p90": 0.24,
            "passes_completed_pct": 0.18,
            "passes_final_third_p90": 0.14,
            "accurate_long_balls_p90": 0.12,
            "interceptions_p90": 0.10,
            "aerials_won_pct": 0.10,
            "blocks_p90": 0.08,
            "duels_won_pct": 0.04,
        },
        "Stopper CB": {
            "tackles_p90": 0.16,
            "interceptions_p90": 0.18,
            "blocks_p90": 0.18,
            "clearances_p90": 0.14,
            "aerials_won_pct": 0.16,
            "duels_won_pct": 0.12,
            "prog_passes_p90": 0.06,
        },
        "Cover CB": {
            "interceptions_p90": 0.22,
            "passes_completed_pct": 0.16,
            "prog_passes_p90": 0.14,
            "prog_carries_p90": 0.12,
            "tackles_p90": 0.12,
            "blocks_p90": 0.10,
            "duels_won_pct": 0.08,
            "aerials_won_pct": 0.06,
        },
    },
    "Verdedigende middenvelder": {
        "Ball Winner 6": {
            "tackles_p90": 0.20,
            "interceptions_p90": 0.20,
            "ball_recoveries_p90": 0.16,
            "duels_won_pct": 0.14,
            "blocks_p90": 0.08,
            "prog_passes_p90": 0.10,
            "passes_completed_pct": 0.08,
            "miscontrols_p90": 0.04,
        },
        "Deep Playmaker 6": {
            "prog_passes_p90": 0.26,
            "passes_final_third_p90": 0.18,
            "passes_completed_pct": 0.16,
            "accurate_long_balls_p90": 0.12,
            "key_passes_p90": 0.08,
            "interceptions_p90": 0.10,
            "miscontrols_p90": 0.05,
            "dispossessed_p90": 0.05,
        },
        "Connector 6": {
            "passes_completed_pct": 0.20,
            "prog_passes_p90": 0.18,
            "carries_p90": 0.12,
            "prog_carries_p90": 0.12,
            "interceptions_p90": 0.12,
            "tackles_p90": 0.10,
            "ball_recoveries_p90": 0.10,
            "miscontrols_p90": 0.06,
        },
    },
    "Nummer 8": {
        "Box to Box": {
            "prog_carries_p90": 0.16,
            "prog_passes_p90": 0.14,
            "tackles_p90": 0.12,
            "interceptions_p90": 0.10,
            "ball_recoveries_p90": 0.10,
            "touches_box_p90": 0.10,
            "xg_p90": 0.10,
            "xa_p90": 0.08,
            "duels_won_pct": 0.10,
        },
        "Ball Carrying 8": {
            "prog_carries_p90": 0.24,
            "take_ons_won_p90": 0.16,
            "dribble_success_pct": 0.10,
            "carries_p90": 0.12,
            "prog_passes_p90": 0.10,
            "xg_p90": 0.08,
            "xa_p90": 0.08,
            "tackles_p90": 0.06,
            "duels_won_pct": 0.06,
        },
        "Playmaking 8": {
            "prog_passes_p90": 0.24,
            "passes_final_third_p90": 0.18,
            "passes_completed_pct": 0.14,
            "key_passes_p90": 0.12,
            "xa_p90": 0.10,
            "prog_carries_p90": 0.08,
            "interceptions_p90": 0.08,
            "miscontrols_p90": 0.06,
        },
    },
    "Nummer 10": {
        "Creative 10": {
            "xa_p90": 0.20,
            "key_passes_p90": 0.20,
            "shot_creating_actions_p90": 0.16,
            "passes_penalty_area_p90": 0.12,
            "prog_passes_p90": 0.10,
            "prog_carries_p90": 0.08,
            "take_ons_won_p90": 0.08,
            "xg_p90": 0.06,
        },
        "Goalscoring 10": {
            "xg_p90": 0.20,
            "goals_p90": 0.18,
            "shots_p90": 0.14,
            "touches_box_p90": 0.14,
            "prog_carries_p90": 0.10,
            "take_ons_won_p90": 0.08,
            "xa_p90": 0.08,
            "key_passes_p90": 0.08,
        },
        "Free 10": {
            "prog_carries_p90": 0.16,
            "take_ons_won_p90": 0.14,
            "key_passes_p90": 0.14,
            "xa_p90": 0.14,
            "shot_creating_actions_p90": 0.14,
            "xg_p90": 0.10,
            "passes_completed_pct": 0.08,
            "dispossessed_p90": 0.10,
        },
    },
    "Winger": {
        "Touchline Winger": {
            "take_ons_won_p90": 0.20,
            "dribble_success_pct": 0.12,
            "prog_carries_p90": 0.20,
            "crosses_p90": 0.14,
            "key_passes_p90": 0.12,
            "xa_p90": 0.10,
            "touches_box_p90": 0.06,
            "dispossessed_p90": 0.06,
        },
        "Inside Forward": {
            "xg_p90": 0.20,
            "goals_p90": 0.16,
            "shots_p90": 0.14,
            "touches_box_p90": 0.14,
            "take_ons_won_p90": 0.12,
            "prog_carries_p90": 0.12,
            "xa_p90": 0.06,
            "dispossessed_p90": 0.06,
        },
        "Creative Winger": {
            "xa_p90": 0.18,
            "key_passes_p90": 0.18,
            "shot_creating_actions_p90": 0.16,
            "passes_penalty_area_p90": 0.10,
            "prog_passes_p90": 0.10,
            "prog_carries_p90": 0.10,
            "take_ons_won_p90": 0.08,
            "crosses_p90": 0.06,
            "dispossessed_p90": 0.04,
        },
        "Pressing Winger": {
            "tackles_p90": 0.14,
            "interceptions_p90": 0.12,
            "ball_recoveries_p90": 0.12,
            "take_ons_won_p90": 0.12,
            "prog_carries_p90": 0.12,
            "xg_p90": 0.10,
            "xa_p90": 0.08,
            "duels_won_pct": 0.10,
            "touches_box_p90": 0.10,
        },
    },
    "Spits": {
        "Poacher": {
            "xg_p90": 0.30,
            "goals_p90": 0.22,
            "shots_p90": 0.18,
            "touches_box_p90": 0.18,
            "shot_creating_actions_p90": 0.06,
            "key_passes_p90": 0.06,
        },
        "Complete Striker": {
            "xg_p90": 0.18,
            "goals_p90": 0.14,
            "shots_p90": 0.12,
            "touches_box_p90": 0.12,
            "xa_p90": 0.10,
            "key_passes_p90": 0.08,
            "prog_carries_p90": 0.08,
            "duels_won_pct": 0.10,
            "take_ons_won_p90": 0.08,
        },
        "Pressing Striker": {
            "tackles_p90": 0.12,
            "interceptions_p90": 0.08,
            "ball_recoveries_p90": 0.12,
            "duels_won_pct": 0.14,
            "xg_p90": 0.18,
            "goals_p90": 0.12,
            "shots_p90": 0.10,
            "touches_box_p90": 0.10,
            "key_passes_p90": 0.04,
        },
        "Link-up Striker": {
            "xa_p90": 0.16,
            "key_passes_p90": 0.14,
            "shot_creating_actions_p90": 0.12,
            "passes_completed_pct": 0.12,
            "duels_won_pct": 0.12,
            "touches_box_p90": 0.10,
            "xg_p90": 0.10,
            "goals_p90": 0.08,
            "prog_passes_p90": 0.06,
        },
    },
}

# =========================================================
# TEAM / LEAGUE STYLE
# =========================================================

ATTRIBUTE_MAP = {
    "technical": [
        "passes_completed_pct",
        "prog_passes_p90",
        "passes_final_third_p90",
        "key_passes_p90",
        "xa_p90",
        "accurate_long_balls_p90",
    ],
    "attacking": [
        "xg_p90",
        "goals_p90",
        "shots_p90",
        "xa_p90",
        "touches_box_p90",
        "key_passes_p90",
        "shot_creating_actions_p90",
    ],
    "tempo": [
        "prog_carries_p90",
        "prog_passes_p90",
        "take_ons_won_p90",
        "carries_p90",
    ],
    "defending": [
        "tackles_p90",
        "interceptions_p90",
        "blocks_p90",
        "ball_recoveries_p90",
    ],
    "physical": [
        "duels_won_pct",
        "aerials_won_pct",
        "aerials_won_p90",
        "dribble_success_pct",
        "prog_carries_p90",
    ],
    "security": [
        "miscontrols_p90",
        "dispossessed_p90",
        "passes_completed_pct",
    ],
}

FEYENOORD_WEIGHTS = {
    "technical": 0.23,
    "attacking": 0.22,
    "tempo": 0.18,
    "defending": 0.15,
    "physical": 0.14,
    "security": 0.08,
}

LEAGUE_STYLE = {
    "Premier League": {"physical": 1.20, "tempo": 1.15, "defending": 1.10, "technical": 1.00, "attacking": 1.00, "security": 1.00},
    "La Liga": {"physical": 0.95, "tempo": 1.00, "defending": 1.00, "technical": 1.18, "attacking": 1.05, "security": 1.10},
    "Bundesliga": {"physical": 1.10, "tempo": 1.18, "defending": 1.05, "technical": 1.00, "attacking": 1.08, "security": 0.95},
    "Serie A": {"physical": 1.00, "tempo": 0.95, "defending": 1.18, "technical": 1.05, "attacking": 1.00, "security": 1.10},
    "Ligue 1": {"physical": 1.18, "tempo": 1.10, "defending": 1.00, "technical": 0.95, "attacking": 1.00, "security": 1.00},
    "Eredivisie": {"physical": 0.90, "tempo": 1.00, "defending": 0.90, "technical": 1.08, "attacking": 1.08, "security": 0.95},
    "Primeira Liga": {"physical": 1.00, "tempo": 1.00, "defending": 1.00, "technical": 1.12, "attacking": 1.05, "security": 1.05},
}

ALL_METRICS = sorted(
    set(m for group in ROLES.values() for role in group.values() for m in role.keys())
    | set(m for metrics in ATTRIBUTE_MAP.values() for m in metrics)
)

# =========================================================
# FBREF PARSING
# =========================================================

def _flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join([str(x) for x in col if str(x) != "nan"]).strip().lower()
            for col in df.columns
        ]
    else:
        df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def _to_float(x):
    try:
        if pd.isna(x):
            return None
        x = str(x).replace("%", "").replace(",", ".").strip()
        if x == "" or x.lower() in ["nan", "none"]:
            return None
        return float(x)
    except Exception:
        return None

def _is_total_or_standard_row(row):
    text = " ".join([str(v).lower() for v in row.values])
    return ("total" in text) or ("2025-2026" in text) or ("2024-2025" in text) or ("squad" not in text)

def _pick_last_numeric_row(df):
    if len(df) == 0:
        return None
    # prefer last row with many numeric cells
    best_i = None
    best_count = -1
    for i in range(len(df)):
        row = df.iloc[i]
        count = sum(_to_float(v) is not None for v in row.values)
        if count > best_count:
            best_count = count
            best_i = i
    return df.iloc[best_i] if best_i is not None else df.iloc[-1]

def _find_col(cols, patterns):
    for pattern in patterns:
        for col in cols:
            if re.search(pattern, col):
                return col
    return None

@st.cache_data(ttl=86400)
def scrape_fbref_player(url):
    """
    One-player, cached FBref import.
    Does not bypass login/paywalls, does not mass scrape.
    """
    if not url or "fbref.com" not in url:
        return {}, "Plak een geldige FBref-spelerlink."

    try:
        time.sleep(2)
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return {}, f"FBref gaf statuscode {r.status_code} terug. Dit betekent meestal dat FBref Streamlit Cloud blokkeert. De app blijft werken: vul de velden handmatig in of gebruik later een andere link."

        html = r.text.replace("<!--", "").replace("-->", "")
        tables = pd.read_html(html)
    except Exception as e:
        return {}, f"Kon FBref niet lezen: {e}"

    data = {}
    found_tables = 0

    for raw_df in tables:
        if raw_df.empty:
            continue

        df = _flatten_columns(raw_df.copy())
        cols = list(df.columns)
        row = _pick_last_numeric_row(df)
        if row is None:
            continue

        found_tables += 1

        # Standard / shooting / passing / possession columns can vary.
        mapping_patterns = {
            "goals_p90": [r"per 90.*gls", r"gls.*90", r"standard_gls"],
            "assists_p90": [r"per 90.*ast", r"ast.*90", r"standard_ast"],
            "xg_p90": [r"per 90.*xg", r"xg.*90", r"expected_xg", r"\bxg\b"],
            "xa_p90": [r"per 90.*xag", r"xag.*90", r"expected_xag", r"\bxag\b", r"\bxa\b"],
            "shots_p90": [r"standard_sh", r"shooting_sh", r"\bsh\b"],
            "passes_attempted_p90": [r"total_att", r"passing_att"],
            "passes_completed_pct": [r"total_cmp%", r"passing_cmp%", r"cmp%"],
            "prog_passes_p90": [r"progression_prgp", r"\bprgp\b"],
            "passes_final_third_p90": [r"1/3", r"final third"],
            "passes_penalty_area_p90": [r"ppa", r"penalty area"],
            "shot_creating_actions_p90": [r"sca.*90", r"sca"],
            "carries_p90": [r"carries"],
            "prog_carries_p90": [r"progression_prgc", r"\bprgc\b"],
            "take_ons_attempted_p90": [r"take-ons_att", r"take.*att"],
            "take_ons_won_p90": [r"take-ons_succ", r"succ"],
            "touches_box_p90": [r"att pen", r"touches_att pen"],
            "tackles_p90": [r"tackles_tkl", r"\btkl\b"],
            "tackles_won_p90": [r"tackles_tklw", r"tklw"],
            "interceptions_p90": [r"\bint\b", r"interceptions"],
            "blocks_p90": [r"blocks_blocks", r"\bblocks\b"],
            "clearances_p90": [r"\bclr\b", r"clearances"],
            "aerials_won_p90": [r"aerial duels_won", r"aerials_won", r"\bwon\b"],
            "aerials_won_pct": [r"aerial duels_won%", r"aerials_won%", r"won%"],
            "miscontrols_p90": [r"carries_mis", r"\bmis\b"],
            "dispossessed_p90": [r"carries_dis", r"\bdis\b"],
        }

        for metric, patterns in mapping_patterns.items():
            col = _find_col(cols, patterns)
            if not col:
                continue
            val = _to_float(row[col])
            if val is None:
                continue

            # FBref standard tables sometimes show totals, not p90.
            # If a column clearly says per 90, use directly.
            # Otherwise we still import as "best effort" because this app is a phone-friendly prototype.
            # User can manually correct values after import.
            if metric not in data:
                data[metric] = val

    if not data:
        return {}, "Geen bruikbare tabellen gevonden. Je kunt de velden handmatig invullen."

    return data, f"{len(data)} velden geïmporteerd uit {found_tables} FBref-tabellen. Controleer ze kort: sommige FBref-tabellen tonen totalen i.p.v. per 90."

# =========================================================
# MODEL FUNCTIONS
# =========================================================

def clamp(value, low=0, high=100):
    return max(low, min(high, value))

def per90_to_score(metric, value):
    low, avg, elite = METRIC_RANGES.get(metric, (0, 50, 100))

    try:
        value = float(value)
    except Exception:
        value = avg

    # higher is better
    if elite > low:
        if value <= low:
            return 0
        if value >= elite:
            return 100
        if value <= avg:
            return 50 * (value - low) / (avg - low)
        return 50 + 50 * (value - avg) / (elite - avg)

    # lower is better
    if value >= low:
        return 0
    if value <= elite:
        return 100
    if value >= avg:
        return 50 * (low - value) / (low - avg)
    return 50 + 50 * (avg - value) / (avg - elite)

def weighted_score(values, weights):
    total = 0
    total_weight = 0
    for metric, weight in weights.items():
        total += per90_to_score(metric, values.get(metric, DEFAULT_VALUES.get(metric, 0))) * weight
        total_weight += abs(weight)
    if total_weight == 0:
        return 50
    return clamp(total / total_weight)

def attribute_score(values, attribute):
    metrics = ATTRIBUTE_MAP.get(attribute, [])
    scores = [per90_to_score(m, values.get(m, DEFAULT_VALUES.get(m, 0))) for m in metrics]
    if not scores:
        return 50
    return clamp(sum(scores) / len(scores))

def calculate_best_role(position, values):
    scores = {}
    for role, weights in ROLES[position].items():
        scores[role] = weighted_score(values, weights)
    best_role = max(scores, key=scores.get)
    return best_role, scores[best_role], scores

def calculate_feyenoord_fit(values):
    score = 0
    for attribute, weight in FEYENOORD_WEIGHTS.items():
        score += attribute_score(values, attribute) * weight
    return clamp(score)

def calculate_league_fit(values, league):
    style = LEAGUE_STYLE[league]
    total = 0
    total_weight = 0
    for attribute, weight in style.items():
        total += attribute_score(values, attribute) * weight
        total_weight += weight
    return clamp(total / total_weight)

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

def color(score):
    if score >= 78:
        return "🟢"
    if score >= 70:
        return "🟡"
    if score >= 62:
        return "🟠"
    return "🔴"

# =========================================================
# SESSION STATE
# =========================================================

if "player_values" not in st.session_state:
    st.session_state["player_values"] = DEFAULT_VALUES.copy()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Spelergegevens")

player = st.sidebar.text_input("Naam speler", "Flávio Nazinho")
position = st.sidebar.selectbox("Positie", list(ROLES.keys()))
league = st.sidebar.selectbox("Huidige competitie", list(LEAGUES.keys()), index=5)
minutes = st.sidebar.number_input("Minuten", min_value=0, max_value=5000, value=1800, step=100)
age = st.sidebar.number_input("Leeftijd", min_value=15, max_value=45, value=22)

st.sidebar.markdown("---")
st.sidebar.header("FBref import")
fbref_url = st.sidebar.text_input("Plak FBref-spelerlink")

col_a, col_b = st.sidebar.columns(2)

with col_a:
    import_clicked = st.button("Haal data op")

with col_b:
    reset_clicked = st.button("Reset data")

if reset_clicked:
    st.session_state["player_values"] = DEFAULT_VALUES.copy()
    st.success("Data gereset naar standaardwaarden.")

if import_clicked:
    scraped, message = scrape_fbref_player(fbref_url)
    if scraped:
        st.session_state["player_values"].update(scraped)
        st.success(message)
    else:
        st.warning(message)

st.sidebar.caption("Tip: controleer na import of waarden per 90 zijn. FBref toont soms totalen afhankelijk van de tabel.")

# =========================================================
# INPUT TABS
# =========================================================

st.markdown("## Data-input")
st.caption("Je kunt alles handmatig overschrijven. De FBref-import vult alleen velden die hij kan vinden.")

tab_attack, tab_pass, tab_carry, tab_def, tab_duel, tab_extra = st.tabs(
    ["Aanval", "Passing", "Carries & dribbels", "Verdedigen", "Duels", "Ratings/extra"]
)

values = st.session_state["player_values"]

def number_metric(metric, label_text=None, help_text=None):
    if label_text is None:
        label_text = metric
    values[metric] = st.number_input(
        label_text,
        min_value=-10.0,
        max_value=200.0,
        value=float(values.get(metric, DEFAULT_VALUES.get(metric, 0))),
        step=0.1,
        help=help_text,
        key=f"input_{metric}",
    )

with tab_attack:
    cols = st.columns(3)
    metrics = [
        "xg_p90", "goals_p90", "shots_p90",
        "xa_p90", "assists_p90", "key_passes_p90",
        "shot_creating_actions_p90", "touches_box_p90", "passes_penalty_area_p90",
    ]
    for i, m in enumerate(metrics):
        with cols[i % 3]:
            number_metric(m)

with tab_pass:
    cols = st.columns(3)
    metrics = [
        "passes_attempted_p90", "passes_completed_pct", "prog_passes_p90",
        "passes_final_third_p90", "accurate_long_balls_p90",
    ]
    for i, m in enumerate(metrics):
        with cols[i % 3]:
            number_metric(m)

with tab_carry:
    cols = st.columns(3)
    metrics = [
        "carries_p90", "prog_carries_p90", "take_ons_attempted_p90",
        "take_ons_won_p90", "dribble_success_pct",
        "crosses_p90", "miscontrols_p90", "dispossessed_p90",
    ]
    for i, m in enumerate(metrics):
        with cols[i % 3]:
            number_metric(m)

with tab_def:
    cols = st.columns(3)
    metrics = [
        "tackles_p90", "tackles_won_p90", "interceptions_p90",
        "blocks_p90", "clearances_p90", "ball_recoveries_p90",
    ]
    for i, m in enumerate(metrics):
        with cols[i % 3]:
            number_metric(m)

with tab_duel:
    cols = st.columns(3)
    metrics = [
        "duels_won_pct", "aerials_won_pct", "aerials_won_p90",
    ]
    for i, m in enumerate(metrics):
        with cols[i % 3]:
            number_metric(m)

with tab_extra:
    cols = st.columns(3)
    metrics = ["fotmob_rating", "sofascore_rating"]
    for i, m in enumerate(metrics):
        with cols[i % 3]:
            number_metric(m)
    st.info("FotMob en SofaScore vul je handmatig in. FBref-import blijft de veilige automatische basis.")

# =========================================================
# CALCULATION
# =========================================================

best_role, role_score, role_scores = calculate_best_role(position, values)
feyenoord_fit = calculate_feyenoord_fit(values)

league_fits = {lg: calculate_league_fit(values, lg) for lg in TOP7_LEAGUES}
best_league = max(league_fits, key=league_fits.get)

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

adjusted_score = clamp((role_score * LEAGUES[league] * minutes_multiplier) + age_bonus)

transfer_rating = clamp(
    adjusted_score * 0.50
    + feyenoord_fit * 0.30
    + league_fits[best_league] * 0.20
)

top5_ready = (
    adjusted_score >= 72
    and feyenoord_fit >= 68
    and max([league_fits[l] for l in ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]]) >= 70
    and minutes >= 1200
)

# =========================================================
# OUTPUT
# =========================================================

st.markdown("---")
st.markdown(f"## Resultaten voor {player}")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Beste rol", best_role)
with c2:
    st.metric("Rolscore", round(role_score, 1))
with c3:
    st.metric("Feyenoord Fit", round(feyenoord_fit, 1))
with c4:
    st.metric("Transfer Rating", round(transfer_rating, 1))

st.info(
    f"{color(transfer_rating)} **{label(transfer_rating)}** — "
    f"Beste rol: **{best_role}** | Beste league-fit: **{best_league}** | "
    f"Top-5 ready: **{'JA' if top5_ready else 'NEE'}**"
)

left, right = st.columns(2)

with left:
    st.markdown("### Rolranking")
    role_df = pd.DataFrame(
        [{"Rol": role, "Score": round(score, 1), "Advies": label(score)}
         for role, score in role_scores.items()]
    ).sort_values("Score", ascending=False)
    st.dataframe(role_df, use_container_width=True)

with right:
    st.markdown("### Top 7 League Fit")
    league_df = pd.DataFrame(
        [{"Competitie": lg, "League Fit": round(score, 1), "Advies": label(score)}
         for lg, score in league_fits.items()]
    ).sort_values("League Fit", ascending=False)
    st.dataframe(league_df, use_container_width=True)

st.markdown("### Attribuutscores")
attr_df = pd.DataFrame(
    [{"Attribuut": attr, "Score": round(attribute_score(values, attr), 1)}
     for attr in ATTRIBUTE_MAP.keys()]
).sort_values("Score", ascending=False)
st.dataframe(attr_df, use_container_width=True)

st.markdown("### Interpretatie")
st.write(
    f"""
**{player}** wordt door het model het best gezien als **{best_role}**.

- **Rolscore:** {round(role_score, 1)}
- **Aangepaste score:** {round(adjusted_score, 1)}
- **Feyenoord Fit:** {round(feyenoord_fit, 1)}
- **Transfer Rating:** {round(transfer_rating, 1)}
- **Beste competitie-fit:** {best_league}
- **Top-5 ready:** {'JA' if top5_ready else 'NEE'}

Gebruik dit als objectieve eerste filter. Daarna moet je nog altijd beelden kijken voor context, rol, tactiek en blessures.
"""
)

with st.expander("Waar haal ik de data gratis vandaan?"):
    st.markdown(
        """
**FBref**
- xG, xAG/xA, shots, passes, progressive passes, carries, tackles, interceptions, aerials, miscontrols, dispossessed.

**FotMob**
- rating, goals, assists, chances created, recoveries.

**SofaScore**
- duels, dribble success, possession lost, long balls.

De automatische import gebruikt alleen publieke FBref-tabellen. Geen login, geen betaalmuur, geen massaal scrapen.
"""
    )
