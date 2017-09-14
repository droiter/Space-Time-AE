from __future__ import division, print_function, absolute_import

import tensorflow as tf

# network architecture definition
NCHANNELS = 1
CONV1 = 128
CONV2 = 64
DECONV1 = 128
DECONV2 = 1
WIDTH = 227
HEIGHT = 227
TVOL = 10

class SpatialTemporalAutoencoder(object):
    def __init__(self, alpha, batch_size, keep_prob):
        self.x_ = tf.placeholder(tf.float32, [-1, TVOL, HEIGHT, WIDTH, NCHANNELS])
        self.y_ = tf.placeholder(tf.float32, [-1, TVOL, HEIGHT, WIDTH, NCHANNELS]) # usually y_ = x_ if reconstruction

        self.batch_size = batch_size
        self.params = {
            'c_w1': tf.Variable(tf.random_normal([11, 11, 1 , 128])),
            'c_b1': tf.Variable(tf.random_normal([128])),
            'c_w2': tf.Variable(tf.random_normal([5, 5, 128, 64])),
            'c_b2': tf.Variable(tf.random_normal([64])),
            'c_w3': tf.Variable(tf.random_normal([5, 5, 64, 128])),
            'c_b3': tf.Variable(tf.random_normal([128])),
            'c_w4': tf.Variable(tf.random_normal([11, 11, 128, 1])),
            'c_b4': tf.Variable(tf.random_normal([1]))
        }

        self.conved = self.spatial_encoder(self.x_)
        self.z = self.temporal_encoder(self.conved)
        self.deconvLSTMed = self.temporal_decoder(self.z)
        self.y = self.spatial_decoder(self.deconvLSTMed)

        self.reconstruction_loss = tf.reduce_mean(tf.pow(self.y_ - self.y, 2))
        self.regularization_loss = tf.constant(0)
        self.loss = self.reconstruction_loss + self.regularization_loss
        self.optimizer = tf.train.AdamOptimizer(alpha).minimize(self.loss)

        self.sess = tf.InteractiveSession()
        self.sess.run(tf.global_variables_initializer())

    @staticmethod
    def conv2d(x, w, b, activation = tf.nn.tanh, strides = 1):
        """
        Build a convolutional layer
        :param x: input
        :param w: filter
        :param b: bias
        :param activation: activation func
        :param strides: the stride when filter is scanning through image
        :return: a convolutional layer representation
        """
        x = tf.nn.conv2d(x, w, strides=[1, strides, strides, 1], padding='VALID')
        x = tf.nn.bias_add(x, b)
        return activation(x)

    @staticmethod
    def deconv2d(x, w, b, out_shape, activation=tf.nn.tanh, strides=1):
        """
        Build a deconvolutional layer
        :param x: input
        :param w: filter
        :param b: bias
        :param out_shape: shape of output tensor
        :param activation: activation func
        :param strides: the stride when filter is scanning
        :return: a deconvolutional layer representation
        """
        x = tf.nn.conv2d_transpose(x, w, output_shape=out_shape, strides=[1, strides, strides, 1], padding='SAME')
        x = tf.nn.bias_add(x, b)
        return activation(x)

    def spatial_encoder(self, x):
        """
        Build a spatial encoder that performs convolutions
        :param x: tensor of input image
        :return: convolved representation
        """
        h, w, c = x.shape[2:]
        x = tf.reshape(x, shape=[-1, h, w, c])
        conv1 = self.conv2d(x, self.params['c_w1'], self.params['c_b1'], activation=tf.nn.tanh, strides=4)
        conv2 = self.conv2d(conv1, self.params['c_w2'], self.params['c_b2'], activation=tf.nn.tanh, strides=2)
        return conv2

    def spatial_decoder(self, x):
        """
        Build a spatial decoder that performs deconvolutions on the input
        :param x: tensor of some transformed representation of input
        :return: deconvolved representation
        """
        h, w, c = x.shape[2:]
        x = tf.reshape(x, shape=[-1, h, w, c])
        deconv1 = self.deconv2d(x, self.params['c_w3'], self.params['c_b3'],
                                [self.batch_size * TVOL, self.params['c_w3'].shape[3], 55, 55],
                                activation=tf.nn.tanh, strides=2)
        deconv2 = self.deconv2d(deconv1, self.params['c_w4'], self.params['c_b4'],
                                [self.batch_size * TVOL, self.params['c_w4'].shape[3], HEIGHT, WIDTH],
                                activation=tf.nn.tanh, strides=4)
        return deconv2

    def temporal_encoder(self, x):
        """
        Build a temporal encoder that performs convLSTM encoding sequential operation
        :param x: convolved representation of input volume
        :return: convolved, convLSTMed representation
        """

        return x

    def temporal_decoder(self, x):
        """
        Build a temporal decoder that performs convLSTM decoder sequential operation
        :param x: convLSTMed representation
        :return: convolved representation
        """
        return x

    def get_loss(self, x, y):
        return self.loss.eval(feed_dict={self.x_: x, self.y_: y}, session=self.sess)