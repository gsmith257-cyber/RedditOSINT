# Reddit OSINT
A tool to help find and collect information on users and communities on Reddit

Prerequisites:
```bash
pip install praw
pip install psaw 
```
You must also have a client secret and client ID from reddit, which you can find here:
https://www.reddit.com/prefs/apps


To run simply execute 'python3 RedditStuff.py'


This tool has three main modes. The first mode is the search for subreddits based on a search term, or terms, provided. The second feature is user search.
This allows for the investigator to see information that isnt noramlly found about a user, such as when the account was created, if it has a verified email, and more.
The last feature is an overlap counter of users using multiple subreddits. An example is if I wanted to know who in the VT Corps of Cadets was on Reddit I could choose
to search for 'VirginiaTech', 'VTCC', and 'ROTC' and it will create a users.txt file of who is uses all of them or just two of them.




Mode three is from https://github.com/Watchful1

This project was originally made in collaberation with ahellerjones for a lab.

Original project here: https://github.com/ahellerjones/CS4984-Project2
