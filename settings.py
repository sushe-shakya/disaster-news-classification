from keras.preprocessing.sequence import pad_sequences
from data_utils.preprocess import preprocess
from keras.models import load_model
from pymongo import MongoClient
from keras import backend as K
from dotenv import load_dotenv
import logging
import pickle
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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


# Load environment variables
ENV = os.getenv("ENV", "local")
load_dotenv(dotenv_path=BASE_DIR + '/config/' + ENV + '.env')

# setup mongo database
setup_db()

tokenizer_file_name = os.getenv("TOKENIZER")
model_file_name = os.getenv("MODEL_NAME")
MAX_SEQUENCE_LENGTH = int(os.getenv("MAX_SEQUENCE_LENGTH"))

index_to_label = load_index_to_label(os.getenv("INDEX_TO_LABEL"))
dnc_model, tokenizer = load_dnc_model(tokenizer_file_name, model_file_name)

if __name__ == '__main__':
    pass
