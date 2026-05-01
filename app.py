import streamlit as st

st.title("⚽ Scouting Model")

player = st.text_input("Player")
league = st.selectbox("League", ["Denmark","Belgium","Netherlands","France","Germany","England","Spain","Italy","Portugal"])
position = st.selectbox("Position", ["Winger","Striker","Midfielder","Fullback"])

goals = st.number_input("Goals p90",0.0,2.0,0.3)
xg = st.number_input("xG p90",0.0,2.0,0.25)
assists = st.number_input("Assists p90",0.0,2.0,0.2)
xa = st.number_input("xA p90",0.0,2.0,0.15)
dribbles = st.number_input("Dribbles p90",0.0,10.0,2.5)
pass_pct = st.number_input("Pass %",0.0,100.0,75.0)
box = st.number_input("Touches box",0.0,15.0,6.0)
duels = st.number_input("Duels won %",0.0,100.0,50.0)

# ROLE
if dribbles > 2.5 and pass_pct < 75:
    role = "Transition Winger"
elif xa > 0.2 and pass_pct > 80:
    role = "Inverted Creator"
elif goals > 0.4:
    role = "Inside Forward"
else:
    role = "Hybrid"

# PLAYER SCORE
if position == "Winger":
    player_score = (goals*20)+(xg*15)+(assists*15)+(dribbles*5)+(box*2)-((100-pass_pct)*0.3)
elif position == "Striker":
    player_score = (goals*25)+(xg*20)+(box*10)-(100-pass_pct)*0.2
elif position == "Midfielder":
    player_score = (xa*15)+(pass_pct*0.3)+(duels*0.2)
else:
    player_score = (dribbles*10)+(pass_pct*0.3)+(duels*0.4)

# LEAGUE FACTOR
factor = {
    "Denmark":0.87,"Belgium":0.92,"Netherlands":0.96,
    "France":1,"Germany":1.05,"England":1.1,
    "Spain":1,"Italy":1,"Portugal":0.95
}
adjusted = player_score * factor[league]

# FEYENOORD FIT
feyenoord = (min(dribbles,3)*15 + min(box,10)*20 + min(pass_pct,80)*15 + min(duels,80)*10)

# TRANSFER
transfer = adjusted*0.4 + feyenoord*0.6

# OUTPUT
st.subheader("Results")
st.write("Role:", role)
st.write("Player Score:", round(player_score,1))
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
