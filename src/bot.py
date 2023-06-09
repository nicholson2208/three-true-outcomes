from mastodon import Mastodon

import os

def test():
    # literally just for testing imports
    print("test")

def send_post(text="Shout out to the three true outcome king of the day", image_path = "", alt=""):
    """
    Sends a post using the bot account I set up
    
    Args:
        text: (str) default = "Shout out to the three true outcome king of the day"
            The text content of of the post
        image_path: (str)
            the path of the stadium image to be included in the post 
        alt: (str)
            alt text for the image
            
    Returns:
        None
    """
    
    #   Set up Mastodon connection

    # I think I also need to use os for an access token directly
    mastodon = Mastodon(
        access_token = os.environ['MASTODON_API_TOKEN'],
        api_base_url = 'https://mast.mastodonsports.social/'
    )
    
    media = mastodon.media_post(image_path, description=alt)
    mastodon.status_post(text, media_ids=media)
    
def send_test_post():
    # I think I also need to use os for an access token directly
    mastodon = Mastodon(
        access_token = os.environ['MASTODON_API_TOKEN'],
        api_base_url = 'https://mast.mastodonsports.social/'
    )
    
    mastodon.status_post("hello again world, from GH actions")

