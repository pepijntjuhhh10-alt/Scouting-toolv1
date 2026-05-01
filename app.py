import streamlit as st

st.title("⚽ Scouting Model PRO")

# =====================
# INPUT
# =====================

player = st.text_input("Player")

league = st.selectbox("League", [
    "Denmark","Belgium","Netherlands","France",
    "Germany","England","Spain","Italy","Portugal"
])

position = st.selectbox("Position", [
    "Goalkeeper",
    "Fullback",
    "Center Back",
    "Defensive Midfielder",
    "Central Midfielder (8)",
    "Attacking Midfielder (10)",
    "Winger",
    "Striker"
])

# Stats
goals = st.number_input("Goals p90",0.0,2.0,0.3)
xg = st.number_input("xG p90",0.0,2.0,0.25)
assists = st.number_input("Assists p90",0.0,2.0,0.2)
xa = st.number_input("xA p90",0.0,2.0,0.15)
dribbles = st.number_input("Dribbles p90",0.0,10.0,2.5)
pass_pct = st.number_input("Pass %",0.0,100.0,75.0)
box = st.number_input("Touches in box",0.0,15.0,6.0)
duels = st.number_input("Duels won %",0.0,100.0,50.0)
tackles = st.number_input("Tackles p90",0.0,10.0,2.0)
interceptions = st.number_input("Interceptions p90",0.0,10.0,1.5)
saves = st.number_input("Saves p90 (GK)",0.0,10.0,3.0)

# =====================
# ROLE DETECTIE
# =====================

role = "Hybrid"

# WINGER
if position == "Winger":
    if dribbles > 3:
        role = "Direct Runner"
    elif dribbles > 2.5 and pass_pct < 75:
        role = "Transition Winger"
    elif xa > 0.25 and pass_pct > 80:
        role = "Inverted Creator"
    elif goals > 0.4:
        role = "Inside Forward"
    else:
        role = "Touchline Winger"

# STRIKER
elif position == "Striker":
    if goals > 0.6:
        role = "Poacher"
    elif duels > 60:
        role = "Target Man"
    elif assists > 0.25:
        role = "Link Forward"
    elif tackles > 1.5:
        role = "Pressing Forward"
    else:
        role = "Complete Forward"

# 10
elif position == "Attacking Midfielder (10)":
    if xa > 0.35:
        role = "Playmaker"
    elif goals > 0.5:
        role = "Shadow Striker"
    elif xa > 0.25:
        role = "Final Third Creator"
    elif dribbles > 2:
        role = "Free Roamer"
    else:
        role = "Goal Threat 10"

# 8
elif position == "Central Midfielder (8)":
    if duels > 60 and tackles > 2:
        role = "Box-to-Box"
    elif pass_pct > 87:
        role = "Tempo Controller"
    elif dribbles > 2:
        role = "Ball Carrier"
    elif xa > 0.2:
        role = "Progressor"
    else:
        role = "Hybrid 8"

# DM
elif position == "Defensive Midfielder":
    if tackles > 3 and interceptions > 2:
        role = "Destroyer"
    elif duels > 65:
        role = "Ball Winner"
    elif pass_pct > 88:
        role = "Deep Playmaker"
    elif pass_pct > 82:
        role = "Controller"
    else:
        role = "Anchor"

# CB
elif position == "Center Back":
    if pass_pct > 87:
        role = "Ball Playing CB"
    elif duels > 70:
        role = "Aerial Dominator"
    elif tackles > 2:
        role = "Defensive Stopper"
    elif dribbles > 1:
        role = "Progressive Carrier"
    else:
        role = "Cover Defender"

# FB
elif position == "Fullback":
    if dribbles > 2.5:
        role = "Wingback"
    elif pass_pct > 85:
        role = "Inverted Fullback"
    elif tackles > 2:
        role = "Defensive Fullback"
    elif dribbles > 2:
        role = "Overlapping Fullback"
    else:
        role = "Progressive Carrier"

# GK
elif position == "Goalkeeper":
    if saves > 4:
        role = "Shot Stopper"
    elif pass_pct > 80:
        role = "Build-up Keeper"
    else:
        role = "Sweeper Keeper"

# =====================
# PLAYER SCORE (0-100)
# =====================

if position == "Winger":
    player_score = goals*30 + xg*25 + assists*20 + dribbles*5 + box*2

elif position == "Striker":
    player_score = goals*40 + xg*30 + box*5

elif position == "Attacking Midfielder (10)":
    player_score = xa*35 + assists*25 + goals*20 + pass_pct*0.2

elif position == "Central Midfielder (8)":
    player_score = pass_pct*0.3 + duels*0.3 + tackles*5 + interceptions*5

elif position == "Defensive Midfielder":
    player_score = tackles*10 + interceptions*10 + duels*0.4 + pass_pct*0.2

elif position == "Center Back":
    player_score = duels*0.5 + pass_pct*0.3 + tackles*5 + interceptions*5

elif position == "Fullback":
    player_score = dribbles*5 + pass_pct*0.3 + duels*0.4 + tackles*3

elif position == "Goalkeeper":
    player_score = saves*10 + pass_pct*0.2

# Clamp
player_score = max(0, min(player_score, 100))

# =====================
# LEAGUE ADJUSTMENT
# =====================

league_factor = {
    "Denmark":0.87,
    "Belgium":0.92,
    "Netherlands":0.96,
    "France":1.00,
    "Germany":1.05,
    "England":1.10,
    "Spain":1.00,
    "Italy":1.00,
    "Portugal":0.95
}

adjusted = player_score * league_factor[league]

# =====================
# FEYENOORD FIT
# =====================

feyenoord = (
    (min(dribbles,3)/3)*20 +
    (min(box,10)/10)*30 +
    (min(pass_pct,80)/80)*20 +
    (min(duels,80)/80)*20 +
    (min(tackles,5)/5)*10
)

# =====================
# TRANSFER SCORE
# =====================

transfer = (adjusted*0.5 + feyenoord*0.5)

# =====================
# OUTPUT
# =====================

st.subheader("Results")

st.write("Role:", role)
st.write("Player Score:", round(player_score,1))
st.write("Adjusted Score:", round(adjusted,1))
st.write("Feyenoord Fit:", round(feyenoord,1))
st.write("Transfer Rating:", round(transfer,1))

if transfer >= 85:
    st.success("MUST BUY")
elif transfer >= 82:
    st.success("AANRADER")
elif transfer >= 78:
    st.warning("RISICO")
else:
    st.error("NIET DOEN")
