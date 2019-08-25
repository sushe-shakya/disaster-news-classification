from settings import tokenizer, dnc_model, MAX_SEQUENCE_LENGTH, index_to_label
from db.news import fetch_all_news, fetch_news_by_type
from keras.preprocessing.sequence import pad_sequences
from data_utils.preprocess import preprocess
from flask import request, Response
from flask_cors import CORS
import numpy as np
import logging
import flask
import os

logger = logging.getLogger(__name__)


def create_route(application):
    """Add api route to the application"""
    application.add_url_rule(rule='/health',
                             view_func=health, methods=['GET'])
    application.add_url_rule(rule='/predict',
                             view_func=predict, methods=['POST'])
    application.add_url_rule(rule='/news/filter',
                             view_func=fetch_news_by_type, methods=['POST'])
    application.add_url_rule(rule='/news',
                             view_func=fetch_all_news, methods=['GET'])
    return application


def init_app():
    """Initialize the flask application"""

    APP_NAME = os.getenv("APP_NAME", "PUSHNOMICS")
    ENV = os.getenv("ENV", "local")

    logger.info('Starting {} in {} mode'.format(APP_NAME, ENV))
    application = flask.Flask(__name__)

    CORS(application)

    application = create_route(application)
    return application


def health():
    """Check the server health"""
    return Response(status=200)


def predict():
    """Predict the class for the given text"""
    if request.json:
        try:

            request_dict = request.json
            text = request_dict["text"]

            logger.info(f'Received text: {text}')
            text = preprocess(text)
            sequence = tokenizer.texts_to_sequences([text])
            padded_sequence = pad_sequences(sequence,
                                            maxlen=MAX_SEQUENCE_LENGTH)

            result = dnc_model.predict(padded_sequence)
            label = index_to_label.get(np.argmax(result))
            return Response(f"Predicted class: {label}", status=200)

        except Exception as e:
            logger.error("Exception: {}".format(e))
    else:
        logger.info("Error in request format")
        return Response("Error in request format", status=500)


# initialize the application
application = init_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0')
