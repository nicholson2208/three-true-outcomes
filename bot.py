from mastodon import Mastodon

#   Set up Mastodon

# I think I also need to use os for an access token directly
mastodon = Mastodon(
    access_token = 'token.secret',
    api_base_url = 'https://mast.mastodonsports.social/'
)

media = mastodon.media_post("test.png", description="Some alt text.")
mastodon.status_post("hello world!")