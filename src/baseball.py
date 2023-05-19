from pybaseball import statcast
from pybaseball import playerid_reverse_lookup
from pybaseball import statcast_batter, spraychart, plot_stadium

import os
import pandas as pd
import requests as re
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage,
                                  AnnotationBbox)

from datetime import datetime, timezone


abbreviation_to_name = {
    "LAA" : "angels",
    "HOU" : "astros",
    "OAK" : "athletics",
    "TOR" : "blue_jays",
    "ATL" : "braves",
    "MIL" : "brewers",
    "STL" : "cardinals",
    "CHC" : "cubs",
    "AZ" : "diamondbacks",
    "LAD" : "dodgers",
    "SF" : "giants",
    "CLE" : "indians",
    "SEA" : "mariners",
    "MIA" : "marlins",
    "NYM" : "mets",
    "WSH" : "nationals",
    "BAL" : "orioles",
    "SD" : "padres",
    "PHI" : "phillies",
    "PIT" : "pirates",
    "TEX" : "rangers",
    "TB" : "rays",
    "BOS" : "red_sox",
    "CIN" : "reds",
    "COL" : "rockies",
    "KC" : "royals",
    "DET" : "tigers",
    "MIN" : "twins",
    "CWS" : "white_sox",
    "NYY" : "yankees",
    "else" : "generic"
}

pitch_abbreviation_to_name = {
    "FF" : "4-Seam Fastball",
    "FA" : "4-Seam Fastball",
    "CU" : "Curveball",
    "CH" : "Changeup",
    "FC" : "Cutter",
    "EP" : "Eephus",
    "FO" : "Forkball",
    "KN" : "Knuckleball",
    "KC" : "Knuckle-curve",
    "SC" : "Screwball",
    "SI" : "Sinker",
    "SL" : "Slider",
    "FS" : "Splitter",
    "FT" : "2-Seam Fastball",
    "ST" : "Sweeper",
    "SV" : "Slurve"
}

mlb_logos = pd.read_csv("./data/team_logos/MLB_Colors_Logos.csv")

def get_three_true_outcomes_events(start_dt = None, end_dt = None):
    """
    
    
    Args:
        start_dt: (str) default = "Shout out to the three true outcome king of the day"
            The text content of of the post
        end_dt: (str)
            the path of the stadium image to be included in the post 
            
    Returns:
        df object that contains all of the events that are three true outcomes
    """    
    df = statcast(start_dt=start_dt, end_dt=start_dt)
    
    tto_events = df.loc[df["events"].isin(["strikeout", "walk", "home_run"])]
    
    print(df)

    
    return tto_events, df
    
    
def get_three_true_outcomes(start_dt=None, end_dt=None, write_to_csv=True):
    """
    
    
    Args:
        text: (str) default = "Shout out to the three true outcome king of the day"
            The text content of of the post
        image_path: (str)
            the path of the stadium image to be included in the post 
        alt: (str)
            alt text for the image
            
    Returns:
        df object that contains all of the events that are 
    """    
    
    tto_events, df = get_three_true_outcomes_events(start_dt= start_dt, end_dt = end_dt)
    
    outcome_counts = tto_events.groupby("batter")["events"].value_counts().unstack(fill_value=0)    
    three_outcomes = outcome_counts.loc[(outcome_counts["home_run"] > 0) & (outcome_counts["strikeout"] > 0) & (outcome_counts["walk"] > 0)]

    # Now try to calculate only three true outcomes
    total_counts = df.groupby("batter")["events"].count()
    three_outcomes = three_outcomes.merge(total_counts, on='batter', how='left')
    
    # filter these
    only_three_outcomes = three_outcomes.loc[three_outcomes[["home_run", "strikeout", "walk"]].sum(axis=1) == three_outcomes["events"]]
    
    # attach the actual player name here
    player_ids = only_three_outcomes.index
    player_names = playerid_reverse_lookup(player_ids, key_type='mlbam')
    
    only_three_outcomes = only_three_outcomes.merge(player_names[["name_first", "name_last", "key_mlbam"]],
                                                left_on='batter',
                                                right_on='key_mlbam',
                                                how="left")
    
    only_three_outcomes["run_date"] = end_dt
    only_three_outcomes["has_been_posted"] = False
    only_three_outcomes["posted_time"] = None
    
    
    if write_to_csv:
        # make this a db as some point?
        only_three_outcomes.to_csv("data/tto.csv", mode="w", index = False)
        tto_events.to_csv("data/tto_events.csv", mode="w", index = False)
    
    return only_three_outcomes, tto_events


def get_next_unposted_row(tto_df):
    """
    checks whether or not this three true outcome has been posted yet
    
    Args:
        tto_df: (DataFrame)
            a data frame containing the details for a three true outcome instance, along with posting info
            
    Returns:
        a row of the data frame or None
    """   
    
    not_yet_posted = tto_df[tto_df["has_been_posted"] == False]

    if not_yet_posted.shape[0] > 0:
        return not_yet_posted.iloc[0]
    
    return None


def get_video_clip_urls(actual_row, tto_events):
    """
    prepares the information needed for a post
    
    Args:
        actual_row: (DataFrame)
            something here
    
    Modifies:
    
    Returns:
        dict with title, alt fields
    """
    # this is the thing we will return
    vid_urls_dict = {}
    
    # filter to just the batter we care about
    sub_data = tto_events.loc[tto_events["batter"] == actual_row.key_mlbam]
    
    bs_game_data_endpoint = "https://baseballsavant.mlb.com/gf?game_pk=" 

    resp = re.get(bs_game_data_endpoint + str(sub_data.game_pk.iloc[0]))
    
    if resp.status_code != 200:
        return {}
        
    resp_json = resp.json()
    
    # this means we have data, but need to find the play ids
    # so at_bat_number is for the whole game, so I can concat the two part of that field to get the whole thing.
    game_data_df = pd.DataFrame(resp_json["team_away"])
    game_data_df = pd.concat([game_data_df, pd.DataFrame(resp_json["team_home"])])

    bs_video_endpoint = "https://baseballsavant.mlb.com/sporty-videos?playId="
    
    for this_at_bat_number in sorted(sub_data.at_bat_number):
        
        # get the data for the whole AB
        this_ab = game_data_df[game_data_df["ab_number"] == this_at_bat_number]

        # the last pitch is what we care about
        last_pitch = this_ab[this_ab["pitch_number"] == this_ab["pitch_number"].max()]
        
        # the url of the clip is just the vid url + play id
        vid_url = bs_video_endpoint + str(last_pitch.play_id.iloc[0])
        vid_urls_dict[str(this_at_bat_number)] = vid_url
        
    return vid_urls_dict
    

def create_image_and_text_for_post(actual_row, tto_events):
    """
    prepares the information needed for a post
    
    Args:
        actual_row: (DataFrame)
            something here
    
    Modifies:
        creates data/image.png
    
    Returns:
        dict with title, alt fields
    """
    
    player_name = actual_row.name_first.capitalize() + " " + actual_row.name_last.capitalize()

    sub_data = tto_events.loc[tto_events["batter"] == actual_row.key_mlbam]

    post = plot_spraychart_and_strikezone(actual_row, tto_events)
    
    # write up the actual text of the post here
    vid_urls_dict = get_video_clip_urls(actual_row, tto_events)
    
    # print(sub_data.game_date.iloc[0])
    # When we re read from a csv, the type of the "game_date" field changes to a string, so just try except?
    game_date = ""
    try:
        game_date = str(sub_data.game_date.iloc[0].date())
    except Exception:
        game_date = str(sub_data.game_date.iloc[0])
        
    description = "Shout-out to " + player_name + ", the three true outcome king of " + game_date + "\n\n"
    description += "See the events here:\n"
    
    for this_at_bat_number in sorted(sub_data.at_bat_number):
        this_pitch_df = sub_data[sub_data["at_bat_number"] == this_at_bat_number].iloc[0]
        
        if this_pitch_df["events"] == "home_run":
            description += "HR; " + str(this_pitch_df["hit_distance_sc"]) \
                + " ft, " + str(this_pitch_df["launch_speed"]) + " mph, " + str(this_pitch_df["launch_angle"]) + "° launch"

        else:
            event = "K" if this_pitch_df["events"] == "strikeout" else "BB"

            try:
                readable_pitch_name = pitch_abbreviation_to_name[this_pitch_df["pitch_type"]]
            except KeyError as e:
                readable_pitch_name = ""

            description += event + "; " + readable_pitch_name + ", " + str(this_pitch_df["release_speed"]) + " mph"
        
        # add the url
        description += "\n" + vid_urls_dict[str(this_at_bat_number)] + "\n\n"
    
    description += "#mlb"
    
    post["description"] = description
    post["key_mlbam"] = actual_row.key_mlbam
    post["run_date"] = actual_row.run_date
    
    return post


def update_records(tto_df, key_mlbam, run_date):
    
    
    tto_df.loc[(tto_df["key_mlbam"] == key_mlbam) & (tto_df["run_date"] == run_date), "has_been_posted"] = True
    tto_df.loc[(tto_df["key_mlbam"] == key_mlbam) & (tto_df["run_date"] == run_date), "posted_time"] = str(datetime.now(timezone.utc))
    
    tto_df.to_csv("data/tto.csv", mode="w", index = False)


def plot_strike_zone(pitch_df: pd.DataFrame, title: str = '', colorby: str = 'pitch_type', annotation: str = None, axis = None) -> None:
    """
    Produces a pitches overlaid on a strike zone using statcast data
    
    Args:
        pitch_df: (pandas.DataFrame)
            StatCast pandas.DataFrame of StatCast batter data
        title: (str), default = ''
            Optional: Title of plot
        colorby: (str), default = 'pitch_type'
            Optional: Which category to color the mark with. 'pitch_type','pitcher', 'description' or a column within data
        legend_title: (str), default = based on colorby
            Optional: Title for the legend
        width: (int), default = 500
            Optional: Width of plot (not counting the legend)
        height: (int), default = 500
            Optional: Height of plot
    Returns:
        A matplotlib.axes.Axes object that was used to generate the pitches overlaid on the strike zone
    """
    
    # some things to auto adjust formatting
    # make the markers really visible when fewer pitches
    alpha_markers = min(0.8, 0.5 + 1 / pitch_df.shape[0])
    alpha_text = alpha_markers + 0.2
    
    # define Matplotlib figure and axis
    if axis is None:
        fig, axis = plt.subplots()

    # add home plate to plot 
    home_plate_coords = [[-0.71, 0], [-0.85, -0.5], [0, -1], [0.85, -0.5], [0.71, 0]]
    plate = Polygon(home_plate_coords,
                edgecolor = 'darkgray',
                facecolor = 'lightgray',
                lw = 2)
    axis.add_patch(plate)
    
    # add strike zone to plot. technically this can vary by batter
    # ignore that for now
    axis.add_patch(Rectangle((-0.71, 1.5), 2*0.71, 2,
                 edgecolor = 'lightgray',
                 fill=False,
                 lw=3))
    
    legend_title = ""
    color_label = ""
    
    # to avoid the SettingWithCopyWarning error
    sub_data = pitch_df.copy().reset_index(drop=True)
    
    if colorby == 'pitch_type':
        color_label = 'pitch_type'
        
        if not legend_title:
            legend_title = 'Pitch Type'
            
    elif colorby == 'description':
        values = sub_data.loc[:, 'description'].str.replace('_', ' ').str.title()
        sub_data.loc[:, 'desc'] = values
        color_label = 'desc'
        
        if not legend_title:
            legend_title = 'Pitch Description'
    elif colorby == 'pitcher':
        color_label = 'player_name'
        
        if not legend_title:
            legend_title = 'Pitcher'
            
    elif colorby == "events":
        # only things where something happened
        sub_data = sub_data[sub_data['events'].notna()]
        sub_data['event'] = sub_data['events'].str.replace('_', ' ').str.title()
        color_label = 'event'
        
        if not legend_title:
            legend_title = 'Outcome'
    
    else:
        color_label = colorby
        if not legend_title:
            legend_title = colorby
        
    scatters = []
    
    for color in sub_data[color_label].unique():
        color_sub_data = sub_data[sub_data[color_label] == color]
        scatters.append(axis.scatter(
            color_sub_data["plate_x"],
            color_sub_data['plate_z'],
            s = 10**2,
            label = pitch_abbreviation_to_name[color] if color_label == 'pitch_type' else color,
            alpha = alpha_markers
        ))

        
        # add an annotation at the center of the marker
        if annotation:
            for i, pitch_coord in zip(color_sub_data.index, zip(color_sub_data["plate_x"], color_sub_data['plate_z'])):
                label_formatted = color_sub_data.loc[i, annotation]
                label_formatted = label_formatted if not pd.isna(label_formatted) else ""
                
                if annotation in ["release_speed", "effective_speed", "launch_speed"] and label_formatted != "":
                    label_formatted = "{:.0f}".format(label_formatted)
                
                axis.annotate(label_formatted,
                            pitch_coord,
                            size = 7,
                            ha = 'center',
                            va = 'center',
                            alpha = alpha_text)

    axis.set_xlim(-4, 4)
    axis.set_ylim(-1.5, 7)
    
    axis.axis('off')

    axis.legend(handles=scatters, title=legend_title, bbox_to_anchor=(0.85, 1), loc='upper left')
    plt.title(title)

    # THIS WILL ONLY WORK FOR THE FIRST PERSON! 

    
def make_tto_strikezone_plot(actual_row, tto_events, axis=None):
    
    batter_df = tto_events[tto_events["batter"] == actual_row["key_mlbam"]]
    batter_name = actual_row.name_first.capitalize() + " " + actual_row.name_last.capitalize()
    
    # define Matplotlib figure and axis
    if axis is None:
        fig, axis = plt.subplots()

    player_id = batter_df.batter.iloc[0]

    get_player_headshot(player_id)

    im = plt.imread("data/headshots/{}.png".format(player_id))

    plot_strike_zone(batter_df, colorby = 'events', annotation = "pitch_type", axis = axis)

    imagebox = OffsetImage(im, zoom=0.4)
    imagebox.image.axes = axis

    ab = AnnotationBbox(imagebox,
                        (0, 1),
                        xycoords='axes fraction',
                        frameon=True,
                        bboxprops=dict(lw=0),
                        box_alignment = (0, 0.95))

    axis.add_artist(ab)
    
    plt.axis("off")

    #plt.show()


def get_player_headshot(mlbam_id, size = 200, file_path = "data/headshots/", file_name = None):
    
    base_img_url = "https://img.mlbstatic.com/mlb-photos/image/upload/w_{size},q_200/v1/people/{mlbam_id}/headshot/silo/current".format(size = size, mlbam_id = mlbam_id)
    
    print(base_img_url)
    
    img_resp = re.get(base_img_url)
    
    if img_resp.status_code != 200:
        print(img_resp.status_code)
        
        return -1
    else:
        os.makedirs(file_path, exist_ok=True)
        
        if file_name is None:
            file_name = str(mlbam_id) + ".png"
            
            
        with open(file_path + file_name, 'wb') as f:
            f.write(img_resp.content)

            
def get_team_logo(mlb_logos, team_abbr, file_path = "./data/team_logos/", file_name = None):
    
    # ok so the one from mlb is svg, and I don't want to deal with that, so use ESPN one
    #base_img_url = mlb_logos.loc[mlb_logos["team_abbr"] == team_abbr, "team_cap_logo_on_dark"].values[0].replace("team-cap-on-dark/", "")
    base_img_url = mlb_logos.loc[mlb_logos["team_abbr"] == team_abbr, "team_scoreboard_logo_espn"].values[0]

    
    print(base_img_url)
    
    img_resp = re.get(base_img_url)
    
    if img_resp.status_code != 200:
        print(img_resp.status_code)
        
        return -1
    else:
        os.makedirs(file_path, exist_ok=True)
        
        if file_name is None:
            file_name = str(team_abbr) + ".png"
            
            
        with open(file_path + file_name, 'wb') as f:
            f.write(img_resp.content)


def plot_spraychart_and_strikezone(actual_row, tto_events):
    
    metadata ={}
    
    player_name = actual_row.name_first.capitalize() + " " + actual_row.name_last.capitalize()
    metadata["player_name"] = player_name

    sub_data = tto_events.loc[tto_events["batter"] == actual_row.key_mlbam]

    title = player_name + " " + "HR(s): " + str(actual_row.home_run) +\
    ", " + "BB(s): " + str(actual_row.walk) + ", and K(s): " + str(actual_row.strikeout)

    metadata["title"] = title

    
    # Abbreviation
    abbv = sub_data.home_team.iloc[0]
    team_nickname = ""
    try:
        team_nickname = abbreviation_to_name[abbv]
    except KeyError:
        team_nickname = abbreviation_to_name["else"]

    # Make alt text
    alt="A figure that includes an outline of the {0} stadium with home runs marked. The title reads {1}".format(abbv, title)
    metadata["alt"] = alt

    
    # so because they used plt.show under the hood, it hangs until you close it
    # turn on interactive mode
    plt.ion()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 10))
    
    make_tto_strikezone_plot(actual_row, tto_events, axis=ax1)
    spraychart1(sub_data, team_nickname, abbv, height = 400, width=400, axis=ax2)
    
    fig.suptitle(title, fontsize=16)

    fig.savefig("data/image.png", metadata = {"alt" : alt}, bbox_inches='tight')
        
    plt.close('all')    # close the figure window
    
    return metadata
  

def spraychart1(data: pd.DataFrame, team_stadium: str, abbv: str, title: str = '', tooltips = None,  # pylint: disable=too-many-arguments
               size: int = 100, colorby: str = 'events', legend_title: str = '', width: int = 500,
               height: int = 500, axis = None):
    """
    Produces a spraychart using statcast data overlayed on specified stadium
    
    Args:
        data: (pandas.DataFrame)
            StatCast pandas.DataFrame of StatCast batter data
        team_stadium: (str)
            Team whose stadium the hits will be overlaid on
        title: (str), default = ''
            Optional: Title of plot
        tooltips: (List[str]), default = None
            Optional: List of variables in data to include as tooltips (Deprecated)
        size: (int), default = 100
            Optional: Size of hit circles on plot
        colorby: (str), default = 'events'
            Optional: Which category to color the mark with. 'events','player', or a column within data
        legend_title: (str), default = based on colorby
            Optional: Title for the legend
        width: (int), default = 500
            Optional: Width of plot (not counting the legend)
        height: (int), default = 500
            Optional: Height of plot
    Returns:
        A matplotlib.axes.Axes object that was used to generate the stadium render and the spraychart
    """
    
    plt.axis("off")

    # pull stadium plot to overlay hits on
    base = plot_stadium(team_stadium, title, width-50, height, axis=axis)
    # tack on the logo too, arguably this should not pull if it exist already, but that's fine?
    get_team_logo(mlb_logos, abbv)

    im = plt.imread("./data/team_logos/{}.png".format(abbv), format="png")
    
    # TODO: make these numbers work better
    ab = AnnotationBbox(OffsetImage(im, zoom=0.15, alpha=0.3),
                        (0.5, 0.65),
                        xycoords='axes fraction',
                        frameon=False,
                        bboxprops=dict(lw=0),
                        box_alignment = (0.5, 0.5))
    base.add_artist(ab)
    
    # only plot pitches where something happened
    sub_data = data.copy().reset_index(drop=True)
    sub_data = sub_data[sub_data['events'].notna()][sub_data['hc_x'].notna()][sub_data['hc_y'].notna()]
    if colorby == 'events':
        sub_data['event'] = sub_data['events'].str.replace('_', ' ').str.title()
        color_label = 'event'
        if not legend_title:
            legend_title = 'Outcome'
    elif colorby == 'player':
        color_label = 'player_name'
        if not legend_title:
            legend_title = 'Player'
    else:
        color_label = colorby
        if not legend_title:
            legend_title = colorby

    # scatter plot of hits
    scatters = []
    for color in sub_data[color_label].unique():
        color_sub_data = sub_data[sub_data[color_label] == color]
        scatters.append(base.scatter(
            color_sub_data["hc_x"], color_sub_data['hc_y'].mul(-1), size, label=color, alpha=0.5
        ))

    if tooltips:
        warnings.warn(
            "Tooltips are disabled in the pyplot version of spraychart and will be removed in the future",
            category=DeprecationWarning
        )

    plt.legend(handles=scatters, title=legend_title, bbox_to_anchor=(.85, 1), loc='upper left')


    
    #plt.draw()

    #plt.show()

    #return base
        