# Author: Matt Nicholson

from src.baseball import *
from src.bot import test, send_post, send_test_post

import os
import pandas as pd
import datetime


def main():
    
    # figure out the date and time to run
    # Github actions will be utc
    run_dt = str(datetime.date.today() + datetime.timedelta(days=-1))
    #run_dt = '2023-04-01'
    
    tto_df = pd.DataFrame()
    tto_events_df = pd.DataFrame()
    
    if os.path.isfile("data/tto.csv") and os.path.isfile("data/tto.csv"):
        # if both there, read them
        tto_df = pd.read_csv("data/tto.csv")
        tto_events_df = pd.read_csv("data/tto_events.csv")

        if tto_df.run_date.max() != run_dt:
            # if old, go do the actions for today, 
            # will overwrite existing csv
            print("tto_df was old, need make them again")
            
            tto_df, tto_events_df = get_three_true_outcomes(start_dt=run_dt, end_dt=run_dt)
        
    else:
        print("tto_df don't exist, making them now")
        tto_df, tto_events_df = get_three_true_outcomes(start_dt=run_dt, end_dt=run_dt)

    row = get_next_unposted_row(tto_df)
    post = {}
    
    if row is not None:
        # there is still stuff to post today
        # to see if there are errors
        print(row)
        
        post = create_image_and_text_for_post(row, tto_events_df)
        print("the thing I am going to try to post says ", post)
    
    else:
        print("there are no more things to post today")
        return    
    
    # change this when I am read to go live
    if True:
        print("making a post")
        send_post(text=post["description"], image_path = "data/image.png", alt=post["alt"])
        # TODO: just assume this works I guess?, I feel like there might be a "failed" message that I should check
        update_records(tto_df, post["key_mlbam"], post["run_date"])
        
    else:
        pass


if __name__ == "__main__":
    main()
