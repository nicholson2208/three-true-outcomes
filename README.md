# three-true-outcomes

A [Mastodon bot](https://mast.mastodonsports.social/@3TrueOutcomes) and [accompanying dashboard](https://mnnicholson.com/three-true-outcomes/) for posting a player who achieved only the three true outcomes in every plate appearance in a given day

## How it works at a very high-level
- runs `main.py` through GitHub Actions
- uses the [`pybaseball`](https://github.com/jldbc/pybaseball) library to collect the information to post
- finds video of each of these events from [Baseball Savant](https://baseballsavant.mlb.com/sporty-videos?play_id=)
- posts with the [Mastodon.py](https://mastodonpy.readthedocs.io/en/stable/) library

## The most recent three-true-outcome player

![](/data/image.png)
