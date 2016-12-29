# coding:utf8
############################################################################
#
# Copyright (c) 2016 ICT MCG Group, Inc. All Rights Reserved
#
###########################################################################
"""
Brief:

Authors: zhouxing(@ict.ac.cn)
Date:    2016/12/20 19:55:08
File:    text_model.py
"""
import sys
from keras.models import Sequential, Model
from keras.layers import Activation, Dense, Dropout, Embedding, Flatten, Input, merge, Convolution1D, AveragePooling1D, MaxPooling1D
from keras.layers.wrappers import TimeDistributed
from keras.layers.advanced_activations import LeakyReLU
from keras.regularizers import l2
from keras.constraints import maxnorm
from keras.optimizers import *
from keras.layers.wrappers import TimeDistributed
from keras.layers import LSTM, GRU, Bidirectional
from keras.layers.normalization import BatchNormalization
from keras import backend as K
from AttentionLayer import AttentionLayer

def TextCNN(graph_in, sequence_length, embedding_dim, filter_sizes, num_filters):
    ''' Convolutional Neural Network, including conv + pooling

    Args:
        sequence_length: 输入的文本长度
        embedding_dim: 词向量维度
        filter_sizes:  filter的高度
        num_filters: filter个数

    Returns:
        features extracted by CNN
    '''
    convs = []
    for fsz in filter_sizes:
        conv = Convolution1D(nb_filter=num_filters,
                         filter_length=fsz,
                         border_mode='valid',
                         activation='relu',
                         subsample_length=1)(graph_in)
        pool = MaxPooling1D()(conv)
        flatten = Flatten()(pool)
        convs.append(flatten)
    if len(filter_sizes)>1:
        out = merge(convs, mode='concat')#(convs)
    else:
        out = convs[0]
    #graph = Model(input=graph_in, output=out)
    return out

def LSTMLayer(graph_in, embed_matrix, embed_input, sequence_length, dropout_prob, hidden_dims, embedding_dim=300, lstm_dim=100):
    #model.add(Bidirectional(GRU(100)))
    #model.add(GRU(50))
    #'''
    lstm = Bidirectional(GRU(lstm_dim, return_sequences=True))(graph_in)
    bi_lstm_out = AttentionLayer(lstm_dim)(lstm)
    bi_lstm_dense = TimeDistributed(Dense(1))(bi_lstm_out)
    bi_lstm_avg = AveragePooling1D()(bi_lstm_dense)
    bi_lstm_flatten = Flatten()(bi_lstm_avg)
    #model.add(Bidirectional(GRU(lstm_dim, return_sequences=True)))
    #model.add(TimeDistributed(Dense(1)))
    #model.add(AveragePooling1D())
    #model.add(Flatten())
    #'''
    #model.add(Dense(hidden_dims))
    #model.add(Dropout(dropout_prob[1]))
    #model.add(Dense(hidden_dims, activation='relu'))
    #model.add(Dropout(dropout_prob[1]))
    #model.add(Activation('relu'))
    #model.add(Dense(1, activation='sigmoid'))
    #model.compile(loss='binary_crossentropy', optimizer='RMSprop', metrics=['accuracy'])
    return bi_lstm_flatten


def KeywordLayer(graph_in, sequence_length, embed_input, embedding_dim, embed_matrix):
    merge_keywords = AveragePooling1D()(graph_in)
    flatten = Flatten()(merge_keywords)
    #graph = Model(input=graph_in, output=flatten)
    #model.add(Embedding(embed_input, embedding_dim, input_length=sequence_length, weights=[embed_matrix]))
    #model.add(AveragePooling1D())
    #model.add(Flatten())
    return flatten

def CNNModel4Text(embed_matrix, embed_input, sequence_length, filter_sizes, num_filters, dropout_prob, hidden_dims, model_variation, embedding_dim=300):
    '''CNN model for text classification

    Args:
        embed_matrix: word embedding matrix
        embed_input: embedding矩阵行数
    '''
    #graph = TextCNN(sequence_length, embedding_dim, filter_sizes, num_filters)
    graph = KeywordLayer(sequence_length, embed_input, embedding_dim, embed_matrix)
    # main sequential model
    model = Sequential()
    # 1. embedding layer
    #'''
    if not model_variation=='CNN-static':
        model.add(Embedding(embed_input, embedding_dim, input_length=sequence_length, weights=[embed_matrix]))
    #model.add(Dropout(dropout_prob[0], input_shape=(sequence_length, embedding_dim)))
    #'''
    # 2. CNN layer
    model.add(graph)
    # 3. Hidden Layer
    model.add(Dense(hidden_dims))
    model.add(Dropout(dropout_prob[1]))
    model.add(Activation('relu'))
    model.add(Dense(1))
    model.add(Activation('sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='RMSprop', metrics=['accuracy'])
    return model

def CNNWithKeywordLayer(embed_matrix, embed_input, sequence_length, keywords_length, filter_sizes, num_filters, dropout_prob, hidden_dims, model_variation, embedding_dim=300):
    ''' 2-way input model: left is cnn for sentence embedding while right is keywords

    '''
    embed1 = Embedding(embed_input, embedding_dim,input_length=sequence_length, weights=[embed_matrix])
    embed2 = Embedding(embed_input, embedding_dim,input_length=keywords_length, weights=[embed_matrix])

    # 1. question model part
    left_input = Input(shape=(sequence_length,))
    left_embed = embed1(left_input)
    right_input = Input(shape=(keywords_length,))
    right_embed = embed2(right_input)

    #question_branch = Sequential()
    left_branch = TextCNN(left_embed, sequence_length, embedding_dim, filter_sizes, num_filters)
    #question_branch.add(cnn_model)
    #question_branch.add(Embedding(embed_input, embedding_dim, input_length=sequence_length, weights=[embed_matrix]))
    #question_branch.add(Dropout(dropout_prob[0], input_shape=(sequence_length, embedding_dim)))

    # 2. keyword model part
    #keyword_branch = Sequential()
    #right_branch = KeywordLayer(right_embed, keywords_length, embed_input, embedding_dim, embed_matrix)

    keyword_branch = LSTMLayer(embed_matrix, embed_input, keywords_length, dropout_prob, hidden_dims, embedding_dim)
    #keyword_branch.add(keyword_model)
    # 3. merge layer
    merged = merge([left_branch, right_branch], mode='concat')
    x = Dense(hidden_dims, activation='relu', W_constraint = maxnorm(3))(merged)
    x = Dropout(0.5)(x)
    final_out = Dense(1, activation='sigmoid')(x)
    final_model = Model(input=[left_input, right_input], output=final_out)
    final_model.compile(loss='binary_crossentropy', optimizer='rmsprop', metrics=['accuracy'])
    return final_model

# vim: set expandtab ts=4 sw=4 sts=4 tw=100:
