#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : Joshua
@Time    : 19-3-14 下午11:33
@File    : textcnn_model.py
@Desc    : TextCNN:
            1. embeddding layers
            2. convolutional layer
            3. max-pooling
            4. softmax layer
"""


import tensorflow as tf
from model_tensorflow.basic_model import BaseModel
import configparser


class Config(object):
    """CNN配置参数"""
    def __init__(self, config_file, section=None):
        config_ = configparser.ConfigParser()
        config_.read(config_file)
        if not config_.has_section(section):
            raise Exception("Section={} not found".format(section))

        self.all_params = {}
        for i in config_.items(section):
            self.all_params[i[0]] = i[1]

        config = config_[section]
        if not config:
            raise Exception("Config file error.")
        self.embedding_dim = config.getint("embedding_dim")                # 词向量维度
        self.sequence_len = config.getint("sequence_len")                  # 序列长度
        self.num_labels = config.getint("num_labels")                      # 类别数
        self.num_filters = config.getint("num_filters")                    # 卷积核数目
        self.vocab_size = config.getint("vocab_size")                      # 卷积核尺寸
        self.hidden_dim = config.getint("hidden_dim")                      # 全连接层神经元
        self.kernel_size = eval(config.get("kernel_size", "[3,4,5]"))      # 卷积核尺寸, a list of int. e.g. [3,4,5]
        self.learning_rate = config.getfloat("learning_rate")
        self.learning_decay_rate = config.getfloat("learning_decay_rate")
        self.learning_decay_steps = config.getint("learning_decay_steps")
        self.train_batch_size = config.getint("train_batch_size")
        self.eval_batch_size = config.getint("eval_batch_size")
        self.test_batch_size = config.getint("test_batch_size")
        self.num_epochs = config.getint("num_epochs")
        self.dropout_keep_prob = config.getfloat("dropout_keep_prob")
        self.eval_every_step = config.getint("eval_every_step")





class TextCNN(BaseModel):
    def __init__(self, config, vocab_size, word_vectors):
        super(TextCNN, self).__init__(config=config, vocab_size=vocab_size, word_vectors=word_vectors)

        # 构建模型
        self.build_model()
        # 初始化保存模型的saver对象
        self.init_saver()

    def build_model(self):
        self.embedding_layer()



        # dropout
        with tf.name_scope("dropout"):
            h_drop = tf.nn.dropout(h_pool_flat, self.keep_prob)

        # 全连接层的输出
        with tf.name_scope("output"):
            output_w = tf.get_variable(
                "output_w",
                shape=[num_filters_total, self.config["num_classes"]],
                initializer=tf.contrib.layers.xavier_initializer())
            output_b = tf.Variable(tf.constant(0.1, shape=[self.config["num_classes"]]), name="output_b")
            self.l2_loss += tf.nn.l2_loss(output_w)
            self.l2_loss += tf.nn.l2_loss(output_b)
            self.logits = tf.nn.xw_plus_b(h_drop, output_w, output_b, name="logits")
            self.predictions = self.get_predictions()

        # 计算交叉熵损失
        self.loss = self.cal_loss() + self.config["l2_reg_lambda"] * self.l2_loss
        # 获得训练入口
        self.train_op, self.summary_op = self.get_train_op()

    def embedding_layer(self):
        """
        词嵌入层
        :return:
        """
        with tf.name_scope("embedding"):
            # 利用预训练的词向量初始化词嵌入矩阵
            if self.word_vectors is not None:
                embedding_w = tf.Variable(tf.cast(self.word_vectors, dtype=tf.float32, name="word2vec"),
                                          name="embedding_w")
            else:
                embedding_w = tf.get_variable("embedding_w", shape=[self.vocab_size, self.config.embedding_dim],
                                          initializer=tf.contrib.layers.xavier_initializer())

            # 利用词嵌入矩阵将输入的数据中的词转换成词向量，
            # 维度[batch_size, sequence_length, embedding_dim]
            embedded_words = tf.nn.embedding_lookup(embedding_w, self.inputs)

            # 卷积操作conv2d的输入是四维[batch_size, sequence_length, embedding_dim, channel],
            # 分别代表着批处理大小、宽度、高度、通道数,因此需要增加维度,设为1,用tf.expand_dims来增大维度
            self.embedded_words_expand = tf.expand_dims(embedded_words, -1)

    def conv_maxpool_layer(self):
        """
        卷积池化层
        :return:
        """
        # 创建卷积和池化层
        pooled_outputs = []
        # 有三种size的filter，3， 4， 5，textCNN是个多通道单层卷积的模型，可以看作三个单层的卷积模型的融合
        for i, filter_size in enumerate(self.config.filter_sizes):
            with tf.name_scope("conv-maxpool-%s" % filter_size):
                # 卷积层，卷积核尺寸为filterSize * embeddingSize，卷积核的个数为numFilters
                # 初始化权重矩阵和偏置
                filter_shape = [filter_size, self.config["embedding_size"], 1, self.config["num_filters"]]
                conv_w = tf.Variable(tf.truncated_normal(filter_shape, stddev=0.1), name="conv_w")
                conv_b = tf.Variable(tf.constant(0.1, shape=[self.config["num_filters"]]), name="conv_b")
                conv = tf.nn.conv2d(
                    embedded_words_expand,
                    conv_w,
                    strides=[1, 1, 1, 1],
                    padding="VALID",
                    name="conv")

                # relu函数的非线性映射
                h = tf.nn.relu(tf.nn.bias_add(conv, conv_b), name="relu")
                # 池化层，最大池化，池化是对卷积后的序列取一个最大值
                pooled = tf.nn.max_pool(
                    h,
                    ksize=[1, self.config["sequence_length"] - filter_size + 1, 1, 1],
                    # ksize shape: [batch, height, width, channels]
                    strides=[1, 1, 1, 1],
                    padding='VALID',
                    name="pool")
                pooled_outputs.append(pooled)  # 将三种size的filter的输出一起加入到列表中

        # 得到CNN网络的输出长度
        num_filters_total = self.config.num_filters * len(self.config.filter_sizes)

        # 池化后的维度不变，按照最后的维度channel来concat
        h_pool = tf.concat(pooled_outputs, 3)

        # 摊平成二维的数据输入到全连接层
        self.pool_flat_output = tf.reshape(h_pool, [-1, num_filters_total])


    def full_connection_layer(self):
        """
        全连接层，后面接dropout以及relu激活
        :return:
        """





class TextCNN(object):
    def __init__(self,
                 config,
                 filter_sizes,
                 num_filters,
                 label_size,
                 learning_rate,
                 learning_decay_rate,
                 learning_decay_steps,
                 batch_size,
                 sentence_len,
                 vocab_size,
                 embed_size,
                 is_training,
                 clip_gradients=5.0):
        self.label_size = label_size
        self.batch_size = batch_size
        self.sentence_len = sentence_len
        self.vocab_size = vocab_size
        self.embed_size = embed_size
        self.is_training_flag = is_training
        self.learning_rate = learning_rate
        self.decay_rate = learning_decay_rate
        self.decay_steps = learning_decay_steps

        self.filter_sizes = filter_sizes  # it is a list of int. e.g. [3,4,5]
        self.num_filters = num_filters
        self.initializer = tf.random_normal_initializer(stddev=0.1)
        self.num_filters_total = self.num_filters * len(filter_sizes)  # how many filters totally.
        self.clip_gradients = clip_gradients

        self.global_step = tf.Variable(0, trainable=False, name="global_step")
        self.epoch_step = tf.Variable(0, trainable=False, name="epoch_step")
        self.epoch_increment = tf.assign(self.epoch_step, tf.add(self.epoch_step, tf.constant(1)))

        self.build_graph()

    def add_placeholders(self):
        self.sentence = tf.placeholder(tf.int32, [None, self.sentence_len], name="sentence")  # X
        self.label = tf.placeholder(tf.int32, [None, ], name="label")  # y:[None,label_size]
        # self.input_y_multilabel = tf.placeholder(tf.float32, [None, self.label_size], name="input_y_multilabel")
        self.dropout_keep_prob = tf.placeholder(tf.float32, name="dropout_keep_prob")



    def init_weights(self):
        """define all weights here"""
        with tf.name_scope("embedding_layer"):
            self.embedding = tf.get_variable("embedding", shape=[self.vocab_size, self.embed_size], initializer=self.initializer)  # [vocab_size,embed_size] tf.random_uniform([self.vocab_size, self.embed_size],-1.0,1.0)
        self.w = tf.get_variable("w", shape=[self.num_filters_total, self.label_size], initializer=self.initializer)  # [embed_size,label_size], w是随机初始化来的
        self.b = tf.get_variable("b", shape=[self.label_size])       # [label_size]

    def inference(self):
        """
        embedding layers
        convolutional layer
        max-pooling
        softmax layer"""
        self.embedded_words = tf.nn.embedding_lookup(self.embedding, self.sentence)

        self.sentence_embeddings_expanded = tf.expand_dims(self.embedded_words, -1)  # [None,sencente_len,embed_size,1]

        # if self.use_mulitple_layer_cnn: # this may take 50G memory.
        #    print("use multiple layer CNN")
        #    h=self.cnn_multiple_layers()
        # else: # this take small memory, less than 2G memory
        print("use single layer CNN")
        h = self.cnn_single_layer()
        # 5. logits(use linear layer)and predictions(argmax)
        with tf.variable_scope('fully_connection_layer'):
            logits = tf.matmul(h, self.w) + self.b  # shape:[None, self.num_classes]==tf.matmul([None,self.embed_size],[self.embed_size,self.num_classes])
        return logits


    def cnn_single_layer(self):
        pooled_outputs = []
        # loop each filter size
        # for each filter, do: convolution-pooling layer, feature shape is 4-d. Feature is a new variable
        # step1.create filters
        # step2.conv (CNN->BN->relu)
        # step3.apply nolinearity(tf.nn.relu)
        # step4.max-pooling(tf.nn.max_pool)
        # step5.dropout
        for i, filter_size in enumerate(self.filter_sizes):
            # with tf.name_scope("convolution-pooling-%s" %filter_size):
            with tf.variable_scope("convolution_pooling_layer_{}".format(filter_size)):
                filter_shape = [filter_size, self.embed_size, 1, self.num_filters]
                # step1.create filter
                filter = tf.get_variable("filter-{}".format(filter_size), filter_shape, initializer=self.initializer)
                # step2.conv operation
                # conv2d ===> computes a 2-D convolution given 4-D `input` and `filter` tensors.
                # *num_filters ---> [1, sentence_len - filter_size + 1, 1, num_filters]
                # *batch_size ---> [batch_size, sentence_len - filter_size + 1, 1, num_filters]
                # 卷积层conv2d函数的参数：
                # 构建卷积核尺寸，输入和输出channel分别为1和num_filters
                # 相当于CNN中的卷积核，它要求是一个Tensor，
                # 具有[filter_height, filter_width, in_channels, out_channels]这样的shape，
                # 具体含义是[卷积核的高度，卷积核的宽度，图像通道数，卷积核个数]，
                # 要求类型与参数input相同，有一个地方需要注意，第三维in_channels，就是参数input的第四维
                # 做完卷积之后，矩阵大小为 [None, sequence_length - filter_size + 1, 1, num_filters]
                # input: [batch, in_height, in_width, in_channels]，
                # filter/kernel: [filter_height, filter_width, in_channels, out_channels]
                # output: 4-D [1,sequence_length-filter_size+1,1,1]，得到的是w.x的部分的值
                conv = tf.nn.conv2d(self.sentence_embeddings_expanded, filter, strides=[1, 1, 1, 1], padding="VALID", name="conv-{}".format(filter_size))  # shape:[batch_size,sequence_length - filter_size + 1,1,num_filters]
                # conv = tf.contrib.layers.batch_norm(conv, is_training=self.is_training_flag, scope='cnn_bn_')

                # step3.apply nolinearity
                # h是最终卷积层的输出，即每个feature map，shape = [batch_size, sentence_len - filter_size + 1, 1, num_filters]
                b = tf.get_variable("b-%s" % filter_size, [self.num_filters])
                h = tf.nn.relu(tf.nn.bias_add(conv, b), "relu")  # shape:[batch_size,sequence_length - filter_size + 1,1,num_filters]. tf.nn.bias_add:adds `bias` to `value`

                # step4.max-pooling.
                # 最大池化, 选取卷积结果的最大值pooled的尺寸为[None, 1, 1, 128](卷积核个数)
                # 本质上是一个特征向量，最后一个维度是特征代表数量
                # 待池化的四维张量，维度是[batch, height, width, channels]
                # 池化窗口大小，长度（大于）等于4的数组，与value的维度对应，
                # 一般为[1,height,width,1]，batch和channels上不池化
                # value: A 4-D `Tensor` with shape `[batch, height, width, channels]
                # ksize: A list of ints that has length >= 4.
                # strides: A list of ints that has length >= 4.
                pooled = tf.nn.max_pool(h, ksize=[1, self.sentence_len - filter_size + 1, 1, 1], strides=[1, 1, 1, 1], padding='VALID', name="pool")  # shape:[batch_size, 1, 1, num_filters].max_pool:performs the max pooling on the input.
                pooled_outputs.append(pooled)
        # step4. combine all pooled features, and flatten the feature.output' shape is a [1,None]
        # 将所有window_size下的feature_vector也组合成一个single vector，作为最后一层softmax的输入
        # shape:[batch_size, 1, 1, num_filters_total]. tf.concat=>concatenates tensors along one dimension.
        # 因为3种filter卷积池化之后是一个scalar, 共有num_filters_total = num_filters * len(filter_sizes)
        # 把每一个max-pooling之后的张量合并起来之后得到一个长向量 [batch_size, num_filters_total]
        self.h_pool = tf.concat(pooled_outputs, 3)
        self.h_pool_flat = tf.reshape(self.h_pool, [-1, self.num_filters_total])  # shape should be:[None,num_filters_total]. here this operation has some result as tf.sequeeze().e.g. x's shape:[3,3];tf.reshape(-1,x) & (3, 3)---->(1,9)

        # step5. add dropout: use tf.nn.dropout
        with tf.name_scope("dropout_layer"):
            h_ = tf.nn.dropout(self.h_pool_flat, keep_prob=self.dropout_keep_prob)  # [None,num_filters_total]
        # h_ = tf.layers.dense(h_, self.num_filters_total, activation=tf.nn.tanh, use_bias=True)
        return h_


    def cnn_multiple_layers(self):
        # loop each filter size
        # for each filter, do: convolution-pooling layer, feature shape is 4-d. Feature is a new variable
        # step1.create filters
        # step2.conv (CNN->BN->relu)
        # step3.apply nolinearity(tf.nn.relu)
        # step4.max-pooling(tf.nn.max_pool)
        # step5.dropout
        pooled_outputs = []
        print("sentence_embeddings_expanded:", self.sentence_embeddings_expanded)
        for i, filter_size in enumerate(self.filter_sizes):
            with tf.variable_scope('cnn_multiple_layers' + "convolution-pooling-%s" % filter_size):
                # Layer1:CONV-RELU
                # 1) CNN->BN->relu
                filter = tf.get_variable("filter-%s" % filter_size, [filter_size, self.embed_size, 1, self.num_filters], initializer=self.initializer)
                conv = tf.nn.conv2d(self.sentence_embeddings_expanded, filter, strides=[1, 1, 1, 1], padding="SAME", name="conv")  # shape:[batch_size,sequence_length - filter_size + 1,1,num_filters]
                conv = tf.contrib.layers.batch_norm(conv, is_training=self.is_training_flag, scope='cnn1')
                print(i, "conv1:", conv)
                b = tf.get_variable("b-%s" % filter_size, [self.num_filters])
                h = tf.nn.relu(tf.nn.bias_add(conv, b), "relu")  # shape:[batch_size,sequence_length,1,num_filters]. tf.nn.bias_add:adds `bias` to `value`

                # 2) CNN->BN->relu
                h = tf.reshape(h, [-1, self.sentence_len, self.num_filters, 1])  # shape:[batch_size,sequence_length,num_filters,1]
                # Layer2:CONV-RELU
                filter2 = tf.get_variable("filter2-%s" % filter_size, [filter_size, self.num_filters, 1, self.num_filters], initializer=self.initializer)
                conv2 = tf.nn.conv2d(h, filter2, strides=[1, 1, 1, 1], padding="SAME", name="conv2")  # shape:[batch_size,sequence_length-filter_size*2+2,1,num_filters]
                conv2 = tf.contrib.layers.batch_norm(conv2, is_training=self.is_training_flag, scope='cnn2')
                print(i, "conv2:", conv2)
                b2 = tf.get_variable("b2-%s" % filter_size, [self.num_filters])
                h = tf.nn.relu(tf.nn.bias_add(conv2, b2), "relu2")  # shape:[batch_size,sequence_length,1,num_filters]. tf.nn.bias_add:adds `bias` to `value`

                # 3. Max-pooling
                pooling_max = tf.squeeze(tf.nn.max_pool(h, ksize=[1, self.sentence_len, 1, 1],strides=[1, 1, 1, 1], padding='VALID', name="pool"))
                # pooling_avg=tf.squeeze(tf.reduce_mean(h,axis=1)) #[batch_size,num_filters]
                print(i, "pooling:", pooling_max)
                # pooling=tf.concat([pooling_max,pooling_avg],axis=1) #[batch_size,num_filters*2]
                pooled_outputs.append(pooling_max)  # h:[batch_size,sequence_length,1,num_filters]
        # concat
        h = tf.concat(pooled_outputs, axis=1)  # [batch_size,num_filters*len(self.filter_sizes)]
        print("h.concat:", h)

        with tf.name_scope("dropout"):
            h = tf.nn.dropout(h, keep_prob=self.dropout_keep_prob)  # [batch_size,sequence_length - filter_size + 1,num_filters]
        return h  # [batch_size,sequence_length - filter_size + 1,num_filters]

    # def loss_multilabel(self, l2_lambda=0.0001):  # 0.0001
    #     with tf.name_scope("loss"):
    #         # let `x = logits`, `z = labels`.
    #         # The logistic loss is:z * -log(sigmoid(x)) + (1 - z) * -log(1 - sigmoid(x))
    #         losses = tf.nn.sigmoid_cross_entropy_with_logits(labels=self.input_y_multilabel, logits=self.logits)
    #         #losses=tf.nn.softmax_cross_entropy_with_logits(labels=self.input__y,logits=self.logits)
    #         #losses=-self.input_y_multilabel*tf.log(self.logits)-(1-self.input_y_multilabel)*tf.log(1-self.logits)
    #         print("sigmoid_cross_entropy_with_logits.losses:", losses)
    #         losses = tf.reduce_sum(losses, axis=1)  # shape=(?,). loss for all data in the batch
    #         loss = tf.reduce_mean(losses)         # shape=().   average loss in the batch
    #         l2_losses = tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'bias' not in v.name]) * l2_lambda
    #         loss = loss+l2_losses
    #     return loss


    def loss(self, l2_lambda=0.0001):  # 0.001
        with tf.name_scope("loss"):
            # input: `logits`:[batch_size, num_classes], and `labels`:[batch_size]
            # output: A 1-D `Tensor` of length `batch_size` of the same type as `logits` with the softmax cross entropy loss.
            self.y_true = tf.one_hot(self.label, self.label_size)
            losses = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=self.label, logits=self.logits)
            # sigmoid_cross_entropy_with_logits.
            # losses=tf.nn.softmax_cross_entropy_with_logits(labels=self.input_y, logits=self.logits)
            loss = tf.reduce_mean(losses)
            l2_losses = tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'bias' not in v.name]) * l2_lambda
            loss = loss + l2_losses
        return loss

    def acc(self):
        self.predictions = tf.argmax(self.logits, 1, name="predictions")  # shape:[None,]
        self.y_pred = tf.one_hot(self.predictions, self.label_size)
        correct_prediction = tf.equal(tf.cast(self.predictions, tf.int32), self.label)
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32), name="accuracy")
        return accuracy

    def train_old(self):
        """based on the loss, use SGD to update parameter"""
        learning_rate = tf.train.exponential_decay(self.learning_rate, self.global_step, self.decay_steps, self.decay_rate, staircase=True)
        train_op = tf.contrib.layers.optimize_loss(self.loss_val, global_step=self.global_step, learning_rate=learning_rate, optimizer="Adam", clip_gradients=self.clip_gradients)
        return train_op

    def train(self):
        """based on the loss, use SGD to update parameter"""
        learning_rate = tf.train.exponential_decay(self.learning_rate, self.global_step, self.decay_steps, self.decay_rate, staircase=True)
        self.learning_rate_= learning_rate
        optimizer = tf.train.AdamOptimizer(learning_rate)
        gradients, variables = zip(*optimizer.compute_gradients(self.loss_val))
        gradients, _ = tf.clip_by_global_norm(gradients, 5.0)
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            train_op = optimizer.apply_gradients(zip(gradients, variables))
        return train_op

    def build_graph(self):
        self.add_placeholders()
        self.init_weights()
        self.logits = self.inference()
        self.loss_val = self.loss()
        self.train_op = self.train()
        self.accuracy = self.acc()


