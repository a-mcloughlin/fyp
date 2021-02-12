import requests
import pandas as pd
import json
import ast
from internal.twitter.auth import run_twitter_request_fetch_tweets, run_twitter_request_fetch_account_info
import internal.twitter.requests as requests
import internal.word_processing.handle_wordlist as handle_wordlist
import internal.word_processing.process_json_tweets as process_json
import internal.data_analysis.detect_emotions as check_emotion
from internal.data_analysis.analyse_sentiment_emotions import evaluate_emotions_sentiment
from internal.machine_learning.analyse_political_leaning import evaluate_politics

ml_model_ibc = None
ml_model_kaggle = None
ml_model_my_set = None

# A class to store result data more efficiently 
class tweetset_result:  
    def __init__(self, tweetsetInfo, most_used_data, political_sentiment_data):  
        self.tweetsetInfo = tweetsetInfo
        self.most_used_data = most_used_data
        self.political_sentiment_data = political_sentiment_data

# A class to store result data more efficiently 
class account_result:  
    def __init__(self, tweetsetInfo, most_used_data, political_sentiment_data, account_data):  
        self.tweetsetInfo = tweetsetInfo
        self.most_used_data = most_used_data
        self.political_sentiment_data = political_sentiment_data
        self.account_data = account_data
        
class tweetset_data:
    def __init__(self, term, word_count, tweet_count, sentiment):  
        self.word_count=word_count
        self.term = term
        self.tweet_count = tweet_count
        self.sentiment = sentiment
        
class most_used_data:
    def __init__(self, most_used_words, most_used_emojis, most_used_hashtags, most_tagged_users, strongest_emotions):  
        self.most_used_words=most_used_words
        self.most_used_emojis=most_used_emojis
        self.most_used_hashtags=most_used_hashtags
        self.most_tagged_users=most_tagged_users
        self.strongest_emotions = strongest_emotions

class political_sentiment_data:
    def __init__(self, dataset_country, prediction, political_leaning_degree):
        self.dataset_country = dataset_country 
        self.prediction = prediction
        self.political_leaning_degree = political_leaning_degree

# Check the type of the request passed - Is it a # or @
def check_type(param):
    if param[0] == '#':
        return 'tag', param[1:]
    elif param[0] == '@':
        return 'usr', param[1:]
    else:
        return None, None

# Return twitter request data based on the search param passed
# This function does not make the request, it only geretaed the data to make the request            
def get_tag_or_usr(param):
    err = None
    url = ''
    while url == '':
        typ, parsed = check_type(param)
        
        if typ == 'tag':
            url = requests.get_tweets_for_tag(parsed)
        elif typ == 'usr':
            url = requests.get_tweets_for_user(parsed)
        elif typ == None:
            err = "noHashorAt"
            url = 'err'
            
    return url, typ, parsed, err
   
def analyse_account(term, country):
    
    url, typ, parsed, err = get_tag_or_usr(term)
    
    if typ == 'tag':
        return "hashNotAt"
    
    if err != None:
        return err
    
    err, tweetset, most_used_words, most_used_emojis, most_used_hashtags, most_tagged_users, word_count, tweet_count = fetch_tweetset_data(url, typ, parsed)
    
    acc_url = requests.get_account_info(parsed)
    data, err = run_twitter_request_fetch_account_info(acc_url, "auth.yaml")
    account_data = process_json.process_user_data(data)
    
    if err != None:
        return err

    dataset_country, statement, political_leaning_degree = evaluate_politics(tweetset, country)
    political_data_info = political_sentiment_data(dataset_country, statement, political_leaning_degree)
    sentiment, strongest_emotions = evaluate_emotions_sentiment(tweetset)
    
    tweetset_info = tweetset_data(term, word_count, tweet_count, sentiment)
    most_used_data_info = most_used_data(most_used_words, most_used_emojis, most_used_hashtags, most_tagged_users, strongest_emotions)
    resultitem = account_result(tweetset_info, most_used_data_info, political_data_info, account_data)
    
    err = None
    if tweet_count < 20:
        err = "InsufficientTweets"
    
    return resultitem, err
    
# Taking a serach input:
# Generate the request url - Run that request
# Get the most used words, word_count, emotion levels and number of tweets
# From that data, get the strongest emotions, the positivity, sentiment
# Return the most used words, the word count, the strongest emotions, the number of tweets and the overall sentiment
def analyse(term, country):
    
    url, typ, parsed, err = get_tag_or_usr(term)
    
    if err != None:
        return err
    
    err, tweetset, most_used_words, most_used_emojis, most_used_hashtags, most_tagged_users, word_count, tweet_count = fetch_tweetset_data(url, typ, parsed)
    
    if err != None:
        return err
    
    dataset_country, statement, political_leaning_degree = evaluate_politics(tweetset, country)
    political_data_info = political_sentiment_data(dataset_country, statement, political_leaning_degree)
    sentiment, strongest_emotions = evaluate_emotions_sentiment(tweetset)
    
    tweetset_info = tweetset_data(term, word_count, tweet_count, sentiment)
    most_used_data_info = most_used_data(most_used_words, most_used_emojis, most_used_hashtags, most_tagged_users, strongest_emotions)
    resultitem = tweetset_result(tweetset_info, most_used_data_info, political_data_info)
    
    err = None
    if tweet_count < 20:
        err = "InsufficientTweets"
    
    return resultitem, err

# Taking in request data, Make a twitter request and return the data about it
# Return the most used words, the number of unique words, the number of tweets and the emotion levels
def fetch_tweetset_data(url, typ, parsed):

    tweets, err = run_twitter_request_fetch_tweets(url, "auth.yaml")
    if err != None:
        return err, None, None, None, None, None, None, None
    
    tweet_list, word_list, emoji_list, hashtag_list, mention_list, tweet_count, last_id = process_json.process_json_tweetset(tweets, [], [], [], [], [])
    
    extra_tweet_count = tweet_count
    for item in range(2):
        if (extra_tweet_count == 100):
            if typ == 'tag':
                next_url = requests.get_tweets_for_tag_maxid(parsed, last_id)
            else:
                next_url = requests.get_tweets_for_usr_maxid(parsed, last_id)
                
            more_tweets, err = run_twitter_request_fetch_tweets(next_url, "auth.yaml")
            if err != None:
                return err, None, None, None, None, None, None, None, None
            
            tweet_list, word_list, emoji_list, hashtag_list, mention_list, extra_tweet_count, last_id = process_json.process_json_tweetset(more_tweets, tweet_list, word_list, emoji_list, hashtag_list, mention_list)
            tweet_count = tweet_count + extra_tweet_count
    
    most_used_words = handle_wordlist.get_n_most_frequent_items(word_list, 5)
    most_used_emojis = handle_wordlist.get_n_most_frequent_items(emoji_list, 5)
    most_used_hashtags = handle_wordlist.get_n_most_frequent_items(hashtag_list, 5)
    most_tagged_users = handle_wordlist.get_n_most_frequent_items(mention_list, 5)
    word_count = handle_wordlist.unique_word_count(word_list)
    return err, tweet_list, most_used_words, most_used_emojis, most_used_hashtags, most_tagged_users, word_count, tweet_count

# When running this file locally through the command line:
# Take user search input
# Make twitter request
# Display nicely formatted response data
if __name__ == "__main__":
    print("Enter the hashtag or user tag to analyse in the form #tag or @user")
    resultitem = analyse_account(input(), "global")
    
    if resultitem == "hashNotAt":
        print("You must enter a @user handle, not a hashtag, please try again")
    elif resultitem == "noHashorAt":
        print("You must enter a #tag or @user")
    elif resultitem == "noTweetsFound":
        print("No tweets found for this query")
    else:
        print("Unique words used in "+str(resultitem.tweetsetInfo.tweet_count)+" tweets: "+resultitem.tweetsetInfo.word_count)
        print("Politics Analysed with a dataset from "+str(resultitem.political_sentiment_data.dataset_country))
        print(resultitem.tweetsetInfo.sentiment)
        print("Strongest Emotions: ")
        for i in resultitem.most_used_data.strongest_emotions:
            print(i.name+" : "+str(i.get_bar_fraction(resultitem.tweetsetInfo.tweet_count)))
        print("Political Leaning : "+str(resultitem.political_sentiment_data.prediction))
        print(resultitem.political_sentiment_data.prediction)
        print("Most Used Words: ")
        for i in resultitem.most_used_data.most_used_words:
            print(i.word+":"+str(i.count))
        print("Most Used Emojis: ")
        for i in resultitem.most_used_data.most_used_emojis:
            print(i.word+":"+str(i.count))
        print("Most Used Hashtags: ")
        for i in resultitem.most_used_data.most_used_hashtags:
            print(i.word+":"+str(i.count))
        print("Most Tagged Users: ")
        for i in resultitem.most_used_data.most_tagged_users:
            print(i.word+":"+str(i.count))
            
        print("Account Verified?      "+str(resultitem.account_data.verified))
        print("Account Name:          "+str(resultitem.account_data.name))
        print("Account Description:   "+str(resultitem.account_data.description))
        print("Account Location:      "+str(resultitem.account_data.location))
        
        print("Account Age:           "+str(resultitem.account_data.age))
        print("Followers Count:       "+str(resultitem.account_data.followers_count))
        print("Following Count:       "+str(resultitem.account_data.following_count))
        print("Tweet Count:           "+str(resultitem.account_data.tweet_count))