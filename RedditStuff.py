import praw
from psaw import PushshiftAPI
import requests
from collections import defaultdict
from datetime import datetime, timedelta
import time
import os
import json


username = input("Enter username: ")
password = input("Enter password: ")
clientID = input("Please enter client ID: ")
clientSecret = input("Please enter client secret: ")


reddit = praw.Reddit(
    client_id=clientID,
    client_secret=clientSecret,
    user_agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
    username=username,
    password=password
)
api = PushshiftAPI(reddit)
'''
takes in the search parameters and the PRAW reddit object (can take in subreddits seperated by ,)
Returns an array of subreddits and a corresponding array of subscriber counts
'''
def mode1(search, reddit):
    userSearch = search
    array = userSearch.split(',')
    listOfSubs = []
    urls = []
    subscribes = []
    for searches in array:
        for subredditor in reddit.subreddits.search(searches):
            listOfSubs.append(subredditor)
        stuffFromSubs = []
    print("Subreddit   Subscriber Count")
    print("----------------------------")
    for s in listOfSubs:
        urls.append(s.url)
        subscribes.append(s.subscribers)
        print(s.url + " " + str(s.subscribers))

'''
takes in the search parameters and the PRAW reddit object
Returns an array of info on the user. NEED TO KNOW HOW YOU WANT TO FORMAT THIS FOR GUI
'''
def mode2(search, reddit):

    userSearch = search
    user = reddit.redditor(userSearch)
    print("Username: " + user.name)
    print("User created time: " + str(user.created))
    print("User ID: " + user.id)
    print("User has verified email: " + str(user.has_verified_email))
    print("User's comment karma: " + str(user.comment_karma))

'''
takes in the search parameters (seperated by ,") and how many days back to search (recommended 180)
Creates and writes to a text file in the current directory
'''
def mode3(search, days):
    print("This mode is from Watchful1")
    subreddits = search.split(',')
    ignored_users = ['[deleted]', 'automoderator']
    lookback_days = days
    min_comments_per_sub = 1
    file_name = "users.txt"

    url = "https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&subreddit={}&before="

    startTime = datetime.utcnow()
    startEpoch = int(startTime.timestamp())
    endTime = startTime - timedelta(days=lookback_days)
    endEpoch = int(endTime.timestamp())
    totalSeconds = startEpoch - endEpoch

    if not os.path.exists("overlap_subreddits"):
        os.makedirs("overlap_subreddits")


    def loadSubredditCommenters(subreddit):
        for filename in os.listdir("overlap_subreddits"):
            if filename.endswith(".txt") and filename.startswith(subreddit):
                count_comments = 0
                with open(os.path.join("overlap_subreddits", filename), 'r') as inputFile:
                    commenters = defaultdict(int)
                    for line in inputFile:
                        items = line.split("	")
                        if len(items) != 2:
                            print(f"Error loading line for {subreddit}: {line}")
                            continue
                        user_comments = int(items[1])
                        commenters[items[0]] = user_comments
                        count_comments += user_comments

                dateString = filename.split("_")[-1][:-4]
                print(f"Loaded {len(commenters)} commenters for subreddit r/{subreddit} through {dateString}")
                dateThrough = datetime.strptime(dateString, '%Y-%m-%d')
                return commenters, int(dateThrough.timestamp()), count_comments

        return None, None, 0


    def saveSubredditCommenters(subreddit, commenters, dateThrough):
        if dateThrough is None:
            return
        # print(f"Saving {len(commenters)} commenters for subreddit r/{subreddit} through {dateThrough.strftime('%Y-%m-%d')}")
        for filename in os.listdir("overlap_subreddits"):
            if filename.endswith(".txt") and filename.startswith(subreddit):
                os.remove(os.path.join("overlap_subreddits", filename))

        with open(os.path.join("overlap_subreddits", f"{subreddit}_{dateThrough.strftime('%Y-%m-%d')}.txt"),
                  'w') as outputFile:
            for commenter, countComments in commenters.items():
                outputFile.write(commenter)
                outputFile.write("	")
                outputFile.write(str(countComments))
                outputFile.write("\n")


    def countCommenters(subreddit):
        commenters, previousEpoch, count = loadSubredditCommenters(subreddit)
        if commenters is None:
            commenters = defaultdict(int)
            previousEpoch = startEpoch
        print(f"Counting commenters in: {subreddit}")
        breakOut = False
        currentDate = None
        while True:
            newUrl = url.format(subreddit) + str(previousEpoch)
            try:
                response = requests.get(newUrl, headers={'User-Agent': "Firefox ofc"})
            except requests.exceptions.ReadTimeout:
                print(
                    f"Pushshift timeout, this usually means pushshift is down. Waiting 5 seconds and trying again: {newUrl}")
                time.sleep(5)
                continue
            try:
                objects = response.json()['data']
            except json.decoder.JSONDecodeError:
                print(
                    f"Decoding error, this usually means pushshift is down. Waiting 5 seconds and trying again: {newUrl}")
                time.sleep(5)
                continue

            time.sleep(1)  # pushshift is ratelimited. If we go too fast we'll get errors

            if len(objects) == 0:
                break
            for object in objects:
                previousEpoch = object['created_utc'] - 1
                if object['author'] not in ignored_users:
                    commenters[object['author']] += 1
                count += 1
                if count % 1000 == 0:
                    currentDatetime = datetime.fromtimestamp(previousEpoch)
                    print("r/{0} comments: {1}, {2}, {3:.2f}%".format(
                        subreddit,
                        count,
                        currentDatetime.strftime("%Y-%m-%d"),
                        ((startEpoch - previousEpoch) / totalSeconds) * 100))
                    if currentDatetime.date() != currentDate:
                        saveSubredditCommenters(subreddit, commenters, currentDatetime)
                        currentDate = currentDatetime.date()
                if previousEpoch < endEpoch:
                    breakOut = True
                    currentDate = datetime.fromtimestamp(previousEpoch).date()
                    break
            if breakOut:
                break
        saveSubredditCommenters(subreddit, commenters, currentDate)
        print(f"Comments: {count}, commenters: {len(commenters)}")
        return commenters


    commenterSubreddits = defaultdict(int)
    for subreddit in subreddits:
        commenters = countCommenters(subreddit)

        for commenter in commenters:
            if commenters[commenter] >= min_comments_per_sub:
                commenterSubreddits[commenter] += 1

    sharedCommenters = defaultdict(list)
    for commenter, countSubreddits in commenterSubreddits.items():
        if countSubreddits >= len(subreddits) - 2:
            sharedCommenters[countSubreddits].append(commenter)

    commentersAll = len(sharedCommenters[len(subreddits)])
    commentersMinusOne = len(sharedCommenters[len(subreddits) - 1])
    commentersMinusTwo = len(sharedCommenters[len(subreddits) - 2])

    print(
        f"{commentersAll} commenters in all subreddits, {commentersMinusOne} in all but one, {commentersMinusTwo} in all but 2")

    with open(file_name, 'w') as txt:
        if commentersAll == 0:
            txt.write(f"No commenters in all subreddits\n")
        else:
            txt.write(f"{commentersAll} commenters in all subreddits\n")
            for user in sorted(sharedCommenters[len(subreddits)], key=str.lower):
                txt.write(f"{user}\n")
        txt.write("\n")

        if commentersAll < 10:
            if commentersMinusOne == 0:
                txt.write(f"No commenters in all but one subreddits\n")
            else:
                txt.write(f"{commentersMinusOne} commenters in all but one subreddits\n")
                for user in sorted(sharedCommenters[len(subreddits) - 1], key=str.lower):
                    txt.write(f"{user}\n")
            txt.write("\n")

            if commentersMinusOne < 10:
                if commentersMinusTwo == 0:
                    txt.write(f"No commenters in all but two subreddits\n")
                else:
                    txt.write(f"{commentersMinusTwo} commenters in all but two subreddits\n")
                    for user in sorted(sharedCommenters[len(subreddits) - 2], key=str.lower):
                        txt.write(f"{user}\n")
                txt.write("\n")

constant = 1

while (constant == 1):
    mode = int(input("choose mode, 1 = subreddit search, 2 = user search, 3 = subreddit user overlap finder, or 4 = exit: "))

    if mode == 1:
        subred = input("Enter the topic or topics to search for (Seperated by a ,): ")
        mode1(subred, reddit)

    elif mode == 2:
        user = input("Enter username to search: ")
        mode2(user, reddit)

    elif mode == 3:
        search = input("Enter subreddits to compare users for (seperated by ,): ")
        days = input("Enter how many days back you want to search (Suggested: 180): ")
        mode3(search, int(days))
    elif mode == 4:
        exit()
    else:
        print("Please enter a valid option.")