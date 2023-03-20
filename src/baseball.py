from pybaseball import statcast
from pybaseball import playerid_reverse_lookup
from pybaseball import statcast_batter, spraychart

import pandas as pd
import matplotlib.pyplot as plt


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
    
    return tto_events, df
    
    
def get_three_true_outcomes(start_dt=None, end_dt=None):
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

    title = player_name + " " + "HR(s): " + str(actual_row.home_run) +\
    ", " + "BB(s): " + str(actual_row.walk) + ", and K(s): " + str(actual_row.strikeout)

    # Abbreviation
    abbv = sub_data.home_team.iloc[0]

    team_nickname = ""
    try:
        team_nickname = abbreviation_to_name[abbv]
    except KeyError:
        team_nickname = abbreviation_to_name["else"]

    # Make alt text
    alt="A figure that includes an outline of the {0} stadium with home runs marked. The title reads {1}".format(abbv, title)

    
    # so because they used plt.show under the hood, it hangs until you close it
    # turn on interactive mode
    plt.ion()
    
    ax = spraychart(sub_data, team_nickname, title = title, height = 400, width=400)

    ax.figure.savefig("data/image.png", metadata = {"alt" : alt})
    plt.close('all')    # close the figure window
    
    post = {"title" : title, 
            "alt" : alt, 
            "key_mlbam" : actual_row.key_mlbam, 
            "run_date" : actual_row.run_date}
    
    return post


def update_records(tto_df, key_mlbam, run_date):
    
    
    tto_df.loc[(tto_df["key_mlbam"] == key_mlbam) & (tto_df["run_date"] == run_date), "has_been_posted"] = True
    tto_df.loc[(tto_df["key_mlbam"] == key_mlbam) & (tto_df["run_date"] == run_date), "posted_time"] = "now"
    
    tto_df.to_csv("data/tto.csv", mode="w", index = False)

    
