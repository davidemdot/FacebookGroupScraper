# Facebook Group Scraper
Save in a CSV file threads with their comments, and associated data, of a Facebook group (**even closed groups where you are not an admin** but a member).

## Usage
Just download the file `fb_group_scraper.py` and run the script:
```sh
$ python fb_group_scraper.py <group_id> <access_token> [max_threads]
```

### Group ID
You usually can find the group ID looking on your browser. If you access to the chosen group, you will see an URL like `https://www.facebook.com/groups/1234567890`, where the group ID is `1234567890`. In the case of there is no number, try with a tool like [Lookup-ID.com](https://lookup-id.com).

### Access Token
Moreover, you will need an access token to use this script. Go to the [Graph API Explorer](https://developers.facebook.com/tools/explorer) and get a `User Access Token`. Pay attention to select the version 2.3, because is the last one that allows get data from a closed group if you are only a member. Select the `user_groups` option and click on the `Get Access Token` button. Then you can see a long alphanumeric word, which will be your token.

### Max Threads
This is an optional argument that limit the amount of threads you can scrape. Note that if there are a lot of posts in the group, the script will require a fairly long time.
