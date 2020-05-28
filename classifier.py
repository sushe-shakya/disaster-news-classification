from keras.preprocessing.sequence import pad_sequences
from data_utils.preprocess import preprocess
from keras.models import load_model
from keras import backend as K
import numpy as np
import pickle
import os
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_SEQUENCE_LENGTH = 100
session = K.get_session()


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
    print(dnc_model.predict(padded_sequence))
    return dnc_model, tokenizer


def classify_news(text):

    with session.as_default():
        with session.graph.as_default():
            text = preprocess(text)
            sequence = tokenizer.texts_to_sequences([text])
            padded_sequence = pad_sequences(sequence,
                                            maxlen=MAX_SEQUENCE_LENGTH)
            result = dnc_model.predict(padded_sequence)
            label = index_to_label.get(np.argmax(result))

    return label


def load_index_to_label(index_to_label_filename):
    fd = open(f"{BASE_DIR}/models/{index_to_label_filename}", 'rb')
    index_to_label = pickle.load(fd)
    return index_to_label


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


tokenizer_file_name = "tokenizer.pkl"
model_file_name = "dnc_model.h5"
MAX_SEQUENCE_LENGTH = 100

index_to_label = load_index_to_label("index_to_label.pkl")
dnc_model, tokenizer = load_dnc_model(tokenizer_file_name, model_file_name)


if __name__ == "__main__":
    text = str(sys.argv[1])
    prediction = classify_news(text)
    print(prediction)