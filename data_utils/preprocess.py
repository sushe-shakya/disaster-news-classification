import re
import validators
import string


def isURL(text):
    return validators.url(text)


def preprocess(text):
    """Text preprocessing module for a list of texts"""

    # Normalizing utf-8 encoding
    # text = text.decode("unicode-escape").encode("utf8").decode("utf8")

    """1. Lowercase the text, strip leading and trailing spaces, tabs,
    new lines, carriage return"""
    text = text.lower().strip(' \t\n\r')

    """Replace escape characteres with spaces and multiple spaces
    with a single one"""
    text = re.sub(' +', ' ', text)

    # 3. Normalizing the digits
    text_tokens = text.split(' ')
    for token in [token for token in text_tokens if token.isdigit()]:
        text = text.replace(token, "D" * len(token))

    # 4. Normalize urls
    text_tokens = text.split(' ')
    for token in [token for token in text_tokens if isURL(token)]:
        text = text.replace(token, 'httpAddress')

    # 5. Normalize username
    text_tokens = text.split(' ')
    for token in [token for token in text_tokens if token[0] == "@" and
                  len(token) > 1]:
        text = text.replace(token, 'usrId')

    # 6. Remove special characters
    punc = '$%^&*()_+-={}[]:"|\'\~`<>/,'
    trans_table = string.punctuation.maketrans(punc, " " * len(punc))
    text = text.translate(trans_table)

    """7. Replace escape characters with spaces and multiple spaces
    with a single one"""
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('\t', ' ')
    text = re.sub(' +', ' ', text)

    return text
