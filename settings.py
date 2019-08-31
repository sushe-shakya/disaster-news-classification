from keras.preprocessing.sequence import pad_sequences
from data_utils.preprocess import preprocess
from dateutil.parser import parse as date_parse
from datetime import datetime, timedelta
from requests_oauthlib import OAuth1
from keras.models import load_model
from pymongo import MongoClient
from keras import backend as K
from dotenv import load_dotenv
import logging.config
import numpy as np
import schedule
import requests
import logging
import pickle
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Load environment variables
ENV = os.getenv("ENV", "local")
load_dotenv(dotenv_path=BASE_DIR + '/config/' + ENV + '.env')
load_dotenv(dotenv_path=BASE_DIR + '/secret_config/' + ENV + '.env')


CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
TWITTER_API = os.getenv("TWITTER_API")
TWEET_SOURCE_USERID = os.getenv("TWEET_SOURCE_USERID").split(',')
shared_components = {'db': None}


def setup_logging(level='INFO'):
    """Setup logging configuration"""

    if not os.path.exists(BASE_DIR + "/logs/"):
        os.mkdir(BASE_DIR + "/logs/")

    if level is not None:
        fmt = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': fmt
                }
            },
            'handlers': {
                'console': {
                    'formatter': 'standard',
                    'class': 'logging.StreamHandler'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'standard',
                    'filename': BASE_DIR + "/logs/pushnomics-ml-v4-train.log",
                    'maxBytes': 1000000,
                    'backupCount': 10
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console', 'file'],
                    'level': level,
                    'propagate': True
                }
            }
        }

        logging.config.dictConfig(config)


def load_dnc_model(tokenizer_file_name: str, model_file_name: str):
    model_path = f"{BASE_DIR}/models"
    fd = open(f"{model_path}/{tokenizer_file_name}", 'rb')
    tokenizer = pickle.load(fd)
    dnc_model = load_model(f"{model_path}/{model_file_name}",
                           custom_objects={'precision': precision,
                                           'recall': recall, 'f1': f1})
    text = "#mh370 airline"
    prcd_text = preprocess(text)
    sequence = tokenizer.texts_to_sequences([prcd_text])
    padded_sequence = pad_sequences(sequence, maxlen=MAX_SEQUENCE_LENGTH)
    dnc_model.predict(padded_sequence)
    return dnc_model, tokenizer


def setup_db():
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DBNAME")
    client = MongoClient(uri)
    db = client[db_name]
    shared_components['db'] = db


def f1(y_true, y_pred):

    p = precision(y_true, y_pred)
    r = recall(y_true, y_pred)
    return 2 * ((p * r) / (p + r + K.epsilon()))


def recall(y_true, y_pred):
    """
    Computes the recall, a metric for multi-label classification of
    how many relevant items are selected.
    """
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall


def precision(y_true, y_pred):
    """
    Computes the precision, a metric for multi-label classification of
    how many selected items are relevant.
    """
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision


def load_index_to_label(index_to_label_filename):
    fd = open(f"{BASE_DIR}/models/{index_to_label_filename}", 'rb')
    index_to_label = pickle.load(fd)
    return index_to_label


def get_required_values(records: list, keys: list):
    result = []
    for a in records:
        result.append({k: v for k, v in a.items() if k in keys})
    return result


def fetch_twitter_news(user_ids=TWEET_SOURCE_USERID, type="latest"):
    """Fetch the latest news tweeted by the given twitter users"""

    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET)

    all_tweets = np.array([])

    logger.info("Fetching tweets from twitter users")

    for user_id in user_ids:
        start = True
        while True:
            try:

                if start:
                    response = requests.get(TWITTER_API, auth=auth, params={
                                            'user_id': user_id, 'count': 200,
                                            'tweet_mode': 'extended'})
                    batch = response.json()

                    if batch:
                        tweets = np.array(batch)
                        start = False
                    else:
                        print("Completed for {}".format(user_id))
                        break
                    max_id = min([a['id'] for a in batch])

                else:

                    response = requests.get(TWITTER_API, auth=auth, params={
                                            'user_id': user_id, 'count': 200,
                                            'max_id': max_id - 1,
                                            'tweet_mode': 'extended'})
                    batch = response.json()

                    if batch:
                        tweets = np.concatenate((tweets, batch))
                    else:
                        print("Completed for {}".format(user_id))
                        break

                    max_id = min([a['id'] for a in batch])

            except Exception as e:
                print(e)
                break

        all_tweets = np.concatenate((all_tweets, tweets))

    documents = []
    for tweet in all_tweets:
        try:
            _ = {}
            tweet_dte_time = date_parse(tweet["created_at"])
            current_date_time = datetime.utcnow()
            current_date = current_date_time.date()
            current_hour = current_date_time.hour

            if type == "latest":
                c1 = tweet_dte_time.date() == current_date
                c2 = tweet_dte_time.date() == current_date - timedelta(days=1)
                c3 = current_hour == 0
                c4 = tweet_dte_time.hour == current_hour - 1

                if (c1 and c4) or (c2 and c3):

                    _["date"] = str(tweet_dte_time.date())
                    _["time"] = str(tweet_dte_time.timetz())

                    _["news"] = tweet["full_text"]
                    _["link"] = tweet["entities"]["urls"][0]['url']
                    _["user_id"] = tweet["user"]["id"]

                    documents.append(_)
            elif type == "all":
                _["date"] = str(tweet_dte_time.date())
                _["time"] = str(tweet_dte_time.timetz())

                _["news"] = tweet["full_text"]
                _["link"] = tweet["entities"]["urls"][0]['url']
                _["user_id"] = tweet["user"]["id"]

                documents.append(_)

        except Exception as e:
            logger.info(f"Exception: {e}")
    return documents


def save_news_to_db(documents: list):
    db = shared_components["db"]
    collection = db.news
    collection.insert(documents)
    logger.info("Saved documents to mongo db successfully")


def classify_news(text):
    text = preprocess(text)
    sequence = tokenizer.texts_to_sequences([text])
    padded_sequence = pad_sequences(sequence,
                                    maxlen=MAX_SEQUENCE_LENGTH)

    result = dnc_model.predict(padded_sequence)
    label = index_to_label.get(np.argmax(result))
    return label


setup_logging()
logger = logging.getLogger(__file__)

# setup mongo database
setup_db()

# fetch the latest tweets
# schedule.every().minute.at(":01").do(fetch_latest_news)
documents = fetch_twitter_news(type="all")

tokenizer_file_name = os.getenv("TOKENIZER")
model_file_name = os.getenv("MODEL_NAME")
MAX_SEQUENCE_LENGTH = int(os.getenv("MAX_SEQUENCE_LENGTH"))

index_to_label = load_index_to_label(os.getenv("INDEX_TO_LABEL"))
dnc_model, tokenizer = load_dnc_model(tokenizer_file_name, model_file_name)


try:
    logger.info("Classifying the news")
    for document in documents:
        news = document["news"]
        document["disasterType"] = classify_news(news)
    logger.info("Classified all news")

    save_news_to_db(documents)
    logger.info("News saved to database successfully")
except Exception as e:
    logger.info(f"Exception {e} ocurred while saving news to database")


if __name__ == '__main__':
    pass
