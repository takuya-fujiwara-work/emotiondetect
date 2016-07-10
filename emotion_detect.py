#!/usr/bin/env python
#! -*- coding: utf-8 -*-

import sys
import numpy as np
import tensorflow as tf
import cv2


NUM_CLASSES = 4
IMAGE_SIZE = 28
IMAGE_PIXELS = IMAGE_SIZE*IMAGE_SIZE*3

def inference(images_placeholder, keep_prob):
    """ モデルを作成する関数

    引数:
      images_placeholder: inputs()で作成した画像のplaceholder
      keep_prob: dropout率のplace_holder

    返り値:
      cross_entropy: モデルの計算結果
    """
    def weight_variable(shape):
      initial = tf.truncated_normal(shape, stddev=0.1)
      return tf.Variable(initial)

    def bias_variable(shape):
      initial = tf.constant(0.1, shape=shape)
      return tf.Variable(initial)

    def conv2d(x, W):
      return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

    def max_pool_2x2(x):
      return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                            strides=[1, 2, 2, 1], padding='SAME')

    x_image = tf.reshape(images_placeholder, [-1, 28, 28, 3])

    with tf.name_scope('conv1') as scope:
        W_conv1 = weight_variable([5, 5, 3, 32])
        b_conv1 = bias_variable([32])
        h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)

    with tf.name_scope('pool1') as scope:
        h_pool1 = max_pool_2x2(h_conv1)

    with tf.name_scope('conv2') as scope:
        W_conv2 = weight_variable([5, 5, 32, 64])
        b_conv2 = bias_variable([64])
        h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)

    with tf.name_scope('pool2') as scope:
        h_pool2 = max_pool_2x2(h_conv2)

    with tf.name_scope('fc1') as scope:
        W_fc1 = weight_variable([7*7*64, 1024])
        b_fc1 = bias_variable([1024])
        h_pool2_flat = tf.reshape(h_pool2, [-1, 7*7*64])
        h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)
        h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

    with tf.name_scope('fc2') as scope:
        W_fc2 = weight_variable([1024, NUM_CLASSES])
        b_fc2 = bias_variable([NUM_CLASSES])

    with tf.name_scope('softmax') as scope:
        y_conv=tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)

    return y_conv

images_placeholder = tf.placeholder("float", shape=(None, IMAGE_PIXELS))
labels_placeholder = tf.placeholder("float", shape=(None, NUM_CLASSES))
keep_prob = tf.placeholder("float")

logits = inference(images_placeholder, keep_prob)
sess = tf.Session()
saver = tf.train.Saver()
sess.run(tf.initialize_all_variables())
saver.restore(sess, "emotion_detect.ckpt")

def recognize(input):
    result = sess.run(logits, feed_dict={images_placeholder: input, keep_prob: 1.0})
    return result.flatten().tolist()

from flask import Flask, render_template, request
import json
app = Flask(__name__)

@app.route('/emotion')
def emotion_recognition():
	return render_template('index.html')

@app.route('/recognize',methods=['POST'])
def emotion_api():
    if request.headers['Content-Type'] != 'application/json':
        print(request.headers['Content-Type'])
        return flask.jsonify(res='error'), 400
    print request.json
    a = np.array(request.json, dtype=np.uint8).reshape(1, 2352)
    
    if a.size != 2352:
        print a.size
        return flask.jsonify(res='error'), 400

    o = recognize(a)
    print o
    x = np.argsort(o)[::-1]
    print x
    import random

    emotion = ""
    rand = random.randint(0,1)
    print rand
    if x[0] == 0:
        emotion = "cry"
    elif x[0] == 1:
        emotion = "smile"
    elif x[0] == 2:
        emotion = "surprised"
    elif x[0] == 3:
        emotion = "angry"

    result = {
        "result": emotion,
        "rate": [float(round(i, 3)) for i in o] 
    }

    return json.dumps(result)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

