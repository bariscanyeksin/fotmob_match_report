from flask import Flask, render_template, request, flash, make_response, redirect
import pandas as pd
from mplsoccer import Pitch, add_image
from PIL import Image
import urllib.request
from urllib.request import urlopen
import json
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import matplotlib.font_manager as fm
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
import requests
from bs4 import BeautifulSoup

matplotlib.rcParams["figure.dpi"] = 300

fpath = "fonts/Poppins/Poppins-Regular.ttf"
prop = fm.FontProperties(fname=fpath)

fpath_bold = "fonts/Poppins/Poppins-SemiBold.ttf"
prop_bold = fm.FontProperties(fname=fpath_bold)

fpath_bold2 = "fonts/Poppins/Poppins-Bold.ttf"
prop_bold2 = fm.FontProperties(fname=fpath_bold2)

app = Flask(__name__)
app.secret_key = "FotMob_Shotmap"


@app.route("/", methods=["POST", "GET"])
def index():

    json_url = "https://www.fotmob.com/api/leagues?id=71&ccode3=TUR"

    with urllib.request.urlopen(json_url) as url:
        data = json.load(url)
    
    table = data['matches']['allMatches']
    df = pd.json_normalize(table)
    df = df[df['status.reason.longKey'] == 'finished']
    
    match_id_list = []
    mac_metin_list = []
    
    i = 0
    
    while i < len(df):
    
        match_id = df['id'].iloc[i]
    
        ev = df['home.name'].iloc[i]
        dep = df['away.name'].iloc[i]
        skor = df['status.scoreStr'].iloc[i]
        week = df['round'].iloc[i]
    
        mac_metin = "Week " + str(week) + " | " + str(ev) + " " + str(skor) + " " + str(dep) 
    
        match_id_list.append(match_id)
        mac_metin_list.append(mac_metin)
    
        i += 1
    
    merged_list = [(match_id_list[i], mac_metin_list[i]) for i in range(0, len(match_id_list))][::-1]

    choices = merged_list
    selected = request.args.get('choice','1')
    state = {'choice':selected}

    return render_template("index.html", choices=choices, state=state)


@app.route("/plot.png", methods=["POST", "GET"])
def result():
    if request.method == "POST":
        matchId = request.form.get("macId")

        json_url = "https://www.fotmob.com/api/matchDetails?matchId=" + matchId

        with urllib.request.urlopen(json_url) as url:
            data = json.load(url)

        if ((matchId == '') | (matchId == 'selectagame')):
            flash('Match is not selected!')
            return redirect("/")

        else:
            if len(data) == 3:
                flash('Match is not selected!')
                return redirect("/")

            else:
                shotmap_kontrol = pd.DataFrame(
                    data["content"]["shotmap"]["shots"])

                if len(shotmap_kontrol) == 0:
                    flash('Detailed data is not available for the selected match!')
                    return redirect("/")

                else:
                    bilgiler = pd.DataFrame(data["general"])

                    team1id = bilgiler["homeTeam"]["id"]
                    team1name = bilgiler["homeTeam"]["name"]
                    team2id = bilgiler["awayTeam"]["id"]
                    team2name = bilgiler["awayTeam"]["name"]

                    turnuvaID = bilgiler["parentLeagueId"][0]
                    IMAGE_URL_3 = 'https://images.fotmob.com/image_resources/logo/leaguelogo/dark/' + str(turnuvaID) + '.png'
                    logo_3 = Image.open(urlopen(IMAGE_URL_3))

                    skor_bilgisi = data["header"]["status"]
                    skor = str(skor_bilgisi["scoreStr"])

                    tarih_bilgisi = bilgiler["matchTimeUTCDate"][0]
                    tarih_bilgisi = str(tarih_bilgisi[:10])
                    d = datetime.strptime(tarih_bilgisi, '%Y-%m-%d')
                    tarih = d.strftime('%d %B %Y')

                    pozisyon_bilgisi = pd.DataFrame(data["content"]["stats"]["Periods"]["All"]["stats"][0]["stats"][0])
                    pozisyon_1 = pozisyon_bilgisi["stats"][0]
                    pozisyon_2 = pozisyon_bilgisi["stats"][1]

                    bigchances_bilgisi = pd.DataFrame(data["content"]["stats"]["Periods"]["All"]["stats"][0]["stats"][4])
                    bigchances_1 = bigchances_bilgisi["stats"][0]
                    bigchances_2 = bigchances_bilgisi["stats"][1]

                    IMAGE_URL_1 = 'https://images.fotmob.com/image_resources/logo/teamlogo/' + str(team1id) + '.png'
                    logo_1 = Image.open(urlopen(IMAGE_URL_1))
                    IMAGE_URL_2 = 'https://images.fotmob.com/image_resources/logo/teamlogo/' + str(team2id) + '.png'
                    logo_2 = Image.open(urlopen(IMAGE_URL_2))

                    goller = pd.DataFrame(data["header"]["teams"])
                    firstteam_goals = goller.iloc[0]
                    firstteam_goals_1 = str(firstteam_goals["score"])
                    tot_goals_1 = firstteam_goals_1
                    secondteam_goals = goller.iloc[1]
                    secondteam_goals_1 = str(secondteam_goals["score"])
                    tot_goals_2 = secondteam_goals_1

                    df = pd.DataFrame(data["content"]["shotmap"]["shots"])

                    shots1 = df[df["teamId"] == team1id].reset_index()
                    shots2 = df[df["teamId"] == team2id].reset_index()

                    shots2['x'] = 105 - shots2['x']
                    shots2['y'] = 68 - shots2['y']

                    """""
                    shots1_ontarget = shots1[(shots1["isOnTarget"] == True) & (shots1["isBlocked"] == False)] 
                    shots2_ontarget = shots2[(shots2["isOnTarget"] == True) & (shots2["isBlocked"] == False)]
                    shots1_ot = len(shots1_ontarget)
                    shots2_ot = len(shots2_ontarget)
                    """""

                    sot_bilgisi = pd.DataFrame(data["content"]["stats"]["Periods"]["All"]["stats"][1]["stats"][3])
                    shots1_ot = sot_bilgisi["stats"][0]
                    shots2_ot = sot_bilgisi["stats"][1]

                    lig = bilgiler["parentLeagueName"] + " " + bilgiler["parentLeagueSeason"]

                    lig_bilgisi = lig[0]

                    goal_1 = shots1[shots1["eventType"] == "Goal"].copy()
                    miss_1 = shots1[(shots1["eventType"] == "Miss") | (shots1["eventType"] == "Post")].copy()
                    blocked_1 = shots1[shots1["eventType"] == "AttemptSaved"].copy()
                    goal_2 = shots2[shots2["eventType"] == "Goal"].copy()
                    miss_2 = shots2[(shots2["eventType"] == "Miss") | (shots2["eventType"] == "Post")].copy()
                    blocked_2 = shots2[shots2["eventType"] == "AttemptSaved"].copy()

                    toplam_sut_bilgisi = pd.DataFrame(data["content"]["stats"]["Periods"]["All"]["stats"][1]["stats"][1])
                    tot_shots_1 = toplam_sut_bilgisi["stats"][0]
                    tot_shots_2 = toplam_sut_bilgisi["stats"][1]

                    #tot_shots_1 = shots1.shape[0]
                    #xg_1 = shots1["expectedGoals"].sum().round(2)
                    #tot_shots_2 = shots2.shape[0]
                    #xg_2 = shots2["expectedGoals"].sum().round(2)

                    xg_bilgisi = pd.DataFrame(data["content"]["stats"]["Periods"]["All"]["stats"][0]["stats"][1])
                    xg_1 = xg_bilgisi["stats"][0]
                    xg_2 = xg_bilgisi["stats"][1]

                    xgop_bilgisi = pd.DataFrame(data["content"]["stats"]["Periods"]["All"]["stats"][2]["stats"][2])
                    xgop_1 = xgop_bilgisi["stats"][0]
                    xgop_2 = xgop_bilgisi["stats"][1]

                    xgot_bilgisi = data["content"]["stats"]["Periods"]["All"]["stats"][2]["stats"][5]
                    xgot_1 = xgot_bilgisi["stats"][0]
                    xgot_2 = xgot_bilgisi["stats"][1]

                    pitch = Pitch(pitch_type='uefa', pitch_color='#272727', line_color='#818f86', goal_type='box')
                    fig, ax = pitch.draw(figsize=(16, 12.5), constrained_layout=False, tight_layout=True)
                    fig.set_facecolor('#272727')

                    sc_goal_1 = pitch.scatter(goal_1["x"], goal_1["y"],
                                    s=goal_1["expectedGoalsOnTarget"]*1200+100,
                                    c="#ffe11f", alpha=0.9,
                                    marker="*",
                                    ax=ax)

                    sc_goal_2 = pitch.scatter(goal_2["x"], goal_2["y"],
                                    s=goal_2["expectedGoalsOnTarget"]*1200+100,
                                    c="#ffe11f", alpha=0.9,
                                    marker="*",
                                    ax=ax)

                    sc_miss_1 = pitch.scatter(miss_1["x"], miss_1["y"],
                                    s=miss_1["expectedGoals"]*1200+30,
                                    c="#ff2e2e", alpha=0.9,
                                    marker="x",
                                    ax=ax,
                                    edgecolor="#101010")

                    sc_miss_2 = pitch.scatter(miss_2["x"], miss_2["y"],
                                    s=miss_2["expectedGoals"]*1200+30,
                                    c="#ff2e2e", alpha=0.9,
                                    marker="x",
                                    ax=ax,
                                    edgecolor="#101010")

                    sc_blocked_1 = pitch.scatter(blocked_1["x"], blocked_1["y"],
                                    s=blocked_1["expectedGoals"]*1200+50,
                                    c="#5178ad", alpha=0.9,
                                    marker="o",
                                    ax=ax,
                                    edgecolor="#101010")

                    sc_blocked_2 = pitch.scatter(blocked_2["x"], blocked_2["y"],
                                    s=blocked_2["expectedGoals"]*1200+50,
                                    c="#5178ad", alpha=0.9,
                                    marker="o",
                                    ax=ax,
                                    edgecolor="#101010")

                    sc_goal_symbol = pitch.scatter(8.5, -3,
                                    s=600,
                                    c="#ffe11f", alpha=0.9,
                                    marker="*",
                                    ax=ax)

                    sc_blocked_symbol = pitch.scatter(19.5, -3,
                                    s=400,
                                    c="#5178ad", alpha=0.9,
                                    marker="o",
                                    ax=ax,
                                    edgecolor="#101010")

                    sc_miss_symbol = pitch.scatter(38.5, -3,
                                    s=300,
                                    c="#ff2e2e", alpha=0.9,
                                    marker="x",
                                    ax=ax,
                                    edgecolor="#101010")

                    xg_symbol_1 = pitch.scatter(63.7, -3,
                                    s=35,
                                    c="#5178ad", alpha=0.9,
                                    marker="o",
                                    ax=ax,
                                    edgecolor="#101010")

                    xg_symbol_2 = pitch.scatter(65.1, -3,
                                    s=150,
                                    c="#5178ad", alpha=0.9,
                                    marker="o",
                                    ax=ax,
                                    edgecolor="#101010")

                    xg_symbol_3 = pitch.scatter(67.3, -3,
                                    s=400,
                                    c="#5178ad", alpha=0.9,
                                    marker="o",
                                    ax=ax,
                                    edgecolor="#101010")

                    xGOT_symbol_1 = pitch.scatter(78.3, -3,
                                    s=50,
                                    c="#ffe11f", alpha=0.9,
                                    marker="*",
                                    ax=ax)

                    xGOT_symbol_2 = pitch.scatter(79.95, -3,
                                    s=250,
                                    c="#ffe11f", alpha=0.9,
                                    marker="*",
                                    ax=ax)
                    xGOT_symbol_3 = pitch.scatter(82.4, -3,
                                    s=600,
                                    c="#ffe11f", alpha=0.9,
                                    marker="*",
                                    ax=ax)

                    sc_goal_text = ax.text(10.5, -3.43, "Goal", size=15, fontproperties=prop, color='white')
                    sc_blocked_text = ax.text(21.5, -3.43, "Blocked/Saved", size=15, fontproperties=prop, color='white')
                    sc_miss_text = ax.text(40.5, -3.43, "Miss", size=15, fontproperties=prop, color='white')

                    xG_text = ax.text(60.6, -3.43, "xG: ", size=15, fontproperties=prop, color='white')
                    xGOT_text = ax.text(73.1, -3.43, "xGOT: ", size=15, fontproperties=prop, color='white')

                    back_box = dict(boxstyle='round, pad=0.4', facecolor='wheat', alpha=0.9)
                    back_box_2 = dict(boxstyle='round, pad=0.4', facecolor='#facd5c', alpha=0.9)

                    ax.text(52.5, 50.5, "Goals", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
                    ax.text(52.5, 45.5, "xG", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
                    ax.text(52.5, 40.5, "xG Open Play", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
                    ax.text(52.5, 35.5, "xG on Target", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
                    ax.text(52.5, 30.5, "Total Shots", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
                    ax.text(52.5, 25.5, "Shots on Target", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
                    ax.text(52.5, 20.5, "Big Chances", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
                    ax.text(52.5, 15.5, "Possession", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')

                    ax.text(41, 50.5, str(tot_goals_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(41, 45.5, str(xg_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(41, 40.5, str(xgop_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(41, 35.5, str(xgot_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(41, 30.5, str(tot_shots_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(41, 25.5, str(shots1_ot), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(41, 20.5, str(bigchances_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(41, 15.5, str(pozisyon_1)+"%", size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')

                    ax.text(64, 50.5, str(tot_goals_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(64, 45.5, str(xg_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(64, 40.5, str(xgop_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(64, 35.5, str(xgot_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(64, 30.5, str(tot_shots_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(64, 25.5, str(shots2_ot), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(64, 20.5, str(bigchances_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                    ax.text(64, 15.5, str(pozisyon_2)+"%", size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')

                    ax.text(41, 55, str(team1name), size=18, ha="center", fontproperties=prop_bold, color='white')
                    ax.text(64, 55, str(team2name), size=18, ha="center", fontproperties=prop_bold, color='white')

                    ax_image_1 = add_image(logo_1, fig, left=0.37, bottom=0.76, width=0.06, interpolation='hanning')
                    ax_image_2 = add_image(logo_2, fig, left=0.57, bottom=0.76, width=0.06, interpolation='hanning')
                    ax_image_3 = add_image(logo_3, fig, left=0.05, bottom=0.90, width=0.055, interpolation='hanning')

                    ax.legend(facecolor='None', edgecolor='None', labelcolor='white', fontsize=20, loc='lower center', ncol=3, 
                            alignment='center', columnspacing=1, handletextpad=0.4, prop=prop, bbox_to_anchor=(0.5, -0.02))

                    plt.gcf().text(0.0137,0.198, '@bariscanyeksin', va='center', fontsize=15,
                                        fontproperties=prop, color='white', rotation=270)

                    # Set the title
                    fig.text(0.115, 0.945, team1name + " " + skor + " " + team2name, size=30, ha="left", fontproperties=prop_bold, color='white')
                    fig.text(0.115, 0.903, lig_bilgisi + " | " + tarih, size=20, ha="left", fontproperties=prop, color='white')

                    ax.text(94.75, -3.43, "Data: FotMob", size=15, fontproperties=prop, color='white')

                    fig.text(0.075, 0.160, team2name.upper() + " SHOTS", size=14, ha="left", fontproperties=prop_bold2, color='white', alpha=0.5)
                    fig.text(0.925, 0.160, team1name.upper() + " SHOTS", size=14, ha="right", fontproperties=prop_bold2, color='white', alpha=0.5)

                    canvas = FigureCanvas(fig)
                    output = io.BytesIO()
                    canvas.print_png(output)
                    response = make_response(output.getvalue())
                    response.mimetype = 'image/png'
                    return response

if __name__ == '__main__':
    app.run()
