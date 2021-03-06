# -*- coding: utf-8 -*-

"""
    Contains a set of reusable functions to help both training and prediction modules.
"""

import itertools
import re
import nltk
import statistics
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from gensim.models import KeyedVectors
from nltk.corpus import stopwords
from tensorflow.python.keras.preprocessing.sequence import pad_sequences

WORD2VEC_PATH = "./data/GoogleNews-vectors-negative300.bin.gz"
SOURCE_PATH = os.path.dirname(os.path.abspath("src"))
DATA_FILES_PATH = SOURCE_PATH + "/data"
DATA_FILES_TRAINING_PATH = DATA_FILES_PATH + "/training"
DATA_FILES_PREDICTION_PATH = DATA_FILES_PATH + "/prediction"
DATA_FILES_RESULTS_PATH = SOURCE_PATH + "/results"


def make_w2v_embeddings(dataframe, embedding_dim=300, empty_w2v=False):
    vocabs = {}
    vocabs_cnt = 0

    vocabs_not_w2v = {}
    vocabs_not_w2v_cnt = 0

    # Stopwords
    nltk.download('stopwords')
    stops = set(stopwords.words('english'))

    # Load word2vec
    print("Loading word2vec model (it may takes around 2-3 minutes)...")

    if empty_w2v:
        word2vec = EmptyWord2Vec
    else:
        word2vec = KeyedVectors.load_word2vec_format(WORD2VEC_PATH, binary=True)

    print("word2vec loaded")

    for index, row in dataframe.iterrows():
        # Print the number of embedded sentences.
        if index != 0 and index % 1000 == 0:
            print("{:,} sentences embedded.".format(index), flush=True)

        # Iterate through the text of both questions of the row
        for phrase in ['phrase1', 'phrase2']:

            # Question numbers representation
            q2n = []

            for word in __text_to_word_list(row[phrase]):
                # Check for unwanted words
                if word in stops:
                    continue

                # If a word is missing from word2vec model.
                if word not in word2vec.vocab:
                    if word not in vocabs_not_w2v:
                        vocabs_not_w2v_cnt += 1
                        vocabs_not_w2v[word] = 1

                # If you have never seen a word, append it to vocab dictionary.
                if word not in vocabs:
                    vocabs_cnt += 1
                    vocabs[word] = vocabs_cnt
                    q2n.append(vocabs_cnt)
                else:
                    q2n.append(vocabs[word])

            # Append phrase as number representation
            dataframe.at[index, phrase + '_n'] = q2n

    # This will be the embedding matrix
    embeddings = 1 * np.random.randn(len(vocabs) + 1, embedding_dim)

    # The padding will be ignored
    embeddings[0] = 0

    # Build the embedding matrix
    for word, index in vocabs.items():
        if word in word2vec.vocab:
            embeddings[index] = word2vec.word_vec(word)

    del word2vec

    return dataframe, embeddings


def split_and_zero_padding(dataframe, max_seq_length):
    # Split to dicts
    side_phrases = {'left': dataframe['phrase1_n'], 'right': dataframe['phrase2_n']}
    dataset = None

    # Zero padding
    for dataset, side in itertools.product([side_phrases], ['left', 'right']):
        dataset[side] = pad_sequences(dataset[side], padding='pre', truncating='post', maxlen=max_seq_length)

    return dataset


def find_max_seq_length(dataframe):
    max_seq_length = 0

    for column in dataframe[['phrase1_n', 'phrase2_n']]:
        series_phrase = dataframe[column].str.split().str.len()
        max_value = series_phrase.max()
        max_seq_length = (max_value if max_value > max_seq_length else max_seq_length)

    return int(max_seq_length)


def plot_hist_length_dataframe(dataframe, filename):
    data = __phrases_dataframe_size(dataframe)

    plt.figure(figsize=[10, 8])
    plt.hist(x=data, bins=10, color='#D24324', alpha=0.9, rwidth=1)
    plt.xlabel("Sentence Length", fontsize=15)
    # plt.xticks(np.arange(0, max(data) + 1, 20), fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.ylabel("Frequency", fontsize=15)
    plt.title("Sentences Distribution Histogram", fontsize=15)
    plt.legend(handles=__statistics_mpatches(data), handlelength=0, handletextpad=0, fancybox=True)
    plt.savefig(filename)


def __text_to_word_list(text):
    # Pre process and convert texts to a list of words
    text = str(text)
    text = text.lower()

    # Clean the text
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"can't", "cannot ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r",", " ", text)
    text = re.sub(r"\.", " ", text)
    text = re.sub(r"!", " ! ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\^", " ^ ", text)
    text = re.sub(r"\+", " + ", text)
    text = re.sub(r"\-", " - ", text)
    text = re.sub(r"\=", " = ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
    text = re.sub(r":", " : ", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r" u s ", " american ", text)
    text = re.sub(r"\0s", "0", text)
    text = re.sub(r" 9 11 ", "911", text)
    text = re.sub(r"e - mail", "email", text)
    text = re.sub(r"j k", "jk", text)
    text = re.sub(r"\s{2,}", " ", text)

    return text.split()


def __statistics_mpatches(data):
    qnt_patch = mpatches.Patch(label="Qnt. - {qnt}".format(qnt=len(data)))
    min_patch = mpatches.Patch(label="Min. - {min}".format(min=int(min(data))))
    max_patch = mpatches.Patch(label="Max. - {max}".format(max=int(max(data))))
    mean_patch = mpatches.Patch(label="Mean - {:.2f}".format(statistics.mean(data)))
    mode_patch = mpatches.Patch(label="Mode - {mode}".format(mode=statistics.mode(data)))
    median_patch = mpatches.Patch(label="Median - {:.2f}".format(statistics.median(data)))
    stddev_patch = mpatches.Patch(label="Std. Dev. - {:.2f}".format(statistics.stdev(data)))
    variance_patch = mpatches.Patch(label="Variance - {:.2f}".format(statistics.variance(data)))

    patches = [qnt_patch, min_patch, max_patch, mean_patch, mode_patch, median_patch, stddev_patch, variance_patch]

    return patches


def __phrases_dataframe_size(dataframe):
    phrases_size = []

    for column in dataframe[['phrase1_n', 'phrase2_n']]:
        series_phrase = dataframe[column].str.split().str.len().fillna(0)
        phrases_size.extend(series_phrase.tolist())

    # for i, row in dataframe.iterrows():
    #    sentence_length = len(row['phrase1_n'].split()) if row['phrase1_n'] else 0
    #    phrases_size.append(sentence_length)

    #    sentence_length = len(row['phrase2_n'].split()) if row['phrase2_n'] else 0
    #   phrases_size.append(sentence_length)

    return phrases_size


class EmptyWord2Vec:
    vocab = {}
    word_vec = {}
