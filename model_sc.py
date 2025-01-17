import os

import tensorflow as tf
from tensorflow.python.tools import freeze_graph
from tensorflow.tools.graph_transforms import TransformGraph

import config
import download
import loss

from ops import *


class MSINET:
    """The class representing the MSI-Net based on the VGG16 model. It
       implements a definition of the computational graph, as well as
       functions related to network training.
    """

    def __init__(self):
        self._output = None
        self._mapping = {}

        if config.PARAMS["device"] == "gpu":
            self._data_format = "channels_first"
            self._channel_axis = 1
            self._dims_axis = (2, 3)
        elif config.PARAMS["device"] == "cpu":
            self._data_format = "channels_last"
            self._channel_axis = 3
            self._dims_axis = (1, 2)

    def _encoder(self, images):
        """The encoder of the model consists of a pretrained VGG16 architecture
           with 13 convolutional layers. All dense layers are discarded and the
           last 3 layers are dilated at a rate of 2 to account for the omitted
           downsampling. Finally, the activations from 3 layers are combined.

        Args:
            images (tensor, float32): A 4D tensor that holds the RGB image
                                      batches used as input to the network.
        """

        imagenet_mean = tf.constant([103.939, 116.779, 123.68])
        imagenet_mean = tf.reshape(imagenet_mean, [1, 1, 1, 3])

        images -= imagenet_mean

        if self._data_format == "channels_first":
            images = tf.transpose(images, (0, 3, 1, 2))

        layer01 = tf.layers.conv2d(images, 64, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="conv1/conv1_1")

        layer02 = tf.layers.conv2d(layer01, 64, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="conv1/conv1_2")

        layer03 = tf.layers.max_pooling2d(layer02, 2, 2,
                                          data_format=self._data_format)

        layer04 = tf.layers.conv2d(layer03, 128, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="conv2/conv2_1")

        layer05 = tf.layers.conv2d(layer04, 128, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="conv2/conv2_2")

        layer06 = tf.layers.max_pooling2d(layer05, 2, 2,
                                          data_format=self._data_format)

        layer07 = tf.layers.conv2d(layer06, 256, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="conv3/conv3_1")

        layer08 = tf.layers.conv2d(layer07, 256, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="conv3/conv3_2")

        layer09 = tf.layers.conv2d(layer08, 256, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="conv3/conv3_3")

        #layer09_SA = self._google_attention(layer09, channels=256, scope="SA1")

        layer10 = tf.layers.max_pooling2d(layer09, 2, 2,
                                          data_format=self._data_format)

        #layer10_SA = self._google_attention(layer10, channels=256, scope='self_attention_1')

        layer11 = tf.layers.conv2d(layer10, 512, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="conv4/conv4_1")

        layer12 = tf.layers.conv2d(layer11, 512, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="conv4/conv4_2")

        layer13 = tf.layers.conv2d(layer12, 512, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="conv4/conv4_3")

        #ch1 = layer13.get_shape().as_list()[1]
        #layer13_SA = self._google_attention(layer13, channels=ch1, scope="SA2")
                        
        layer14 = tf.layers.max_pooling2d(layer13, 2, 1,
                                          padding="same",
                                          data_format=self._data_format)

        #layer14_SA = self._google_attention(layer14, channels=512, scope='self_attention_2')

        layer15 = tf.layers.conv2d(layer14, 512, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   dilation_rate=2,
                                   data_format=self._data_format,
                                   name="conv5/conv5_1")

        layer16 = tf.layers.conv2d(layer15, 512, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   dilation_rate=2,
                                   data_format=self._data_format,
                                   name="conv5/conv5_2")

        layer17 = tf.layers.conv2d(layer16, 512, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   dilation_rate=2,
                                   data_format=self._data_format,
                                   name="conv5/conv5_3")

        #layer17 = tf.reshape(layer17, shape=[-1, 512, 30, 40])
        #ch2 = layer17.get_shape().as_list()[1]
        #layer17_SA = self._google_attention(layer17, channels=ch2, scope='SA3')
        
        layer18 = tf.layers.max_pooling2d(layer17, 2, 1,
                                          padding="same",
                                          data_format=self._data_format)

        #layer18_SA = self._google_attention(layer18, channels=512, scope='self_attention_3')

        encoder_output = tf.concat([layer10, layer14, layer18],
                                   axis=self._channel_axis)
       
        ch = encoder_output.get_shape().as_list()[1]
        #encoder_output = tf.layers.conv2d(encoder_output, ch, 1, data_format=self._data_format, name="fusion")
        encoder_output = self._google_attention(encoder_output, channels=ch, scope='self_attention')

        self._output = encoder_output
        return layer02, layer05, layer09
        
    def _google_attention(self, x, channels, scope='attention'):
        with tf.variable_scope(scope):
            batch_size, num_channels, height, width = x.get_shape().as_list()
            #print(x.get_shape().as_list())
            #batch_size, num_channels, height, width = tf.shape(x)
            #f = conv(x, channels // 8, kernel=1, stride=1, sn=False, scope='f_conv')  # [bs, h, w, c']
            f = tf.layers.conv2d(x, channels // 8, 1, data_format=self._data_format, name="SA_f"+scope[-1])
            #f = max_pooling(f)
            f = tf.layers.max_pooling2d(f, 2, 2, padding="same", data_format=self._data_format)

            #g = conv(x, channels // 8, kernel=1, stride=1, sn=False, scope='g_conv')  # [bs, h, w, c']
            g = tf.layers.conv2d(x, channels // 8, 1, data_format=self._data_format, name="SA_g"+scope[-1])

            #h = conv(x, channels // 2, kernel=1, stride=1, sn=False, scope='h_conv')  # [bs, h, w, c]
            h = tf.layers.conv2d(x, channels // 2, 1, data_format=self._data_format, name="SA_h"+scope[-1])
            #h = tf.layers.conv2d(x, channels, 1, data_format=self._data_format, name="SA_h"+scope[-1])
            #h = max_pooling(h)
            h = tf.layers.max_pooling2d(h, 2, 2, padding="same", data_format=self._data_format)

            # N = h * w
            f = tf.transpose(f, (0, 2, 3, 1))  # [bs, h, w, c]
            g = tf.transpose(g, (0, 2, 3, 1))
            h = tf.transpose(h, (0, 2, 3, 1))
            
            s = tf.matmul(hw_flatten(g), hw_flatten(f), transpose_b=True)  # # [bs, N, N]
            beta = tf.nn.softmax(s)  # attention map

            o = tf.matmul(beta, hw_flatten(h))  # [bs, N, C]
            o =  tf.transpose(o, (0, 2, 1))   # [bs, C, N]
            gamma = tf.get_variable("gamma"+scope[-1], [1], initializer=tf.constant_initializer(0.0))

            #o = tf.reshape(o, shape=[batch_size, num_channels // 2, height, width])  # [bs, h, w, C]
            o = tf.reshape(o, shape=[tf.shape(x)[0], num_channels // 2, tf.shape(x)[2], tf.shape(x)[3]]) 
            #o = tf.reshape(o, shape=[tf.shape(x)[0], num_channels, tf.shape(x)[2], tf.shape(x)[3]])
            #o = conv(o, channels, kernel=1, stride=1, sn=False, scope='attn_conv')
            o = tf.layers.conv2d(x, channels, 1, data_format=self._data_format, name="SA_o"+scope[-1])
            x = gamma * o + x

        return x
    
    def _attention(self, x, channels, scope='attention'):
        with tf.variable_scope(scope):
            f = conv(x, channels // 8, kernel=1, stride=1, sn=self.sn, scope='f_conv') # [bs, h, w, c']
            g = conv(x, channels // 8, kernel=1, stride=1, sn=self.sn, scope='g_conv') # [bs, h, w, c']
            h = conv(x, channels, kernel=1, stride=1, sn=self.sn, scope='h_conv') # [bs, h, w, c]

            # N = h * w
            s = tf.matmul(hw_flatten(g), hw_flatten(f), transpose_b=True) # # [bs, N, N]

            beta = tf.nn.softmax(s)  # attention map

            o = tf.matmul(beta, hw_flatten(h)) # [bs, N, C]
            gamma = tf.get_variable("gamma", [1], initializer=tf.constant_initializer(0.0))

            o = tf.reshape(o, shape=x.shape) # [bs, h, w, C]
            o = conv(o, channels, kernel=1, stride=1, sn=self.sn, scope='attn_conv')

            x = gamma * o + x

        return x

    def _aspp(self, features):
        """The ASPP module samples information at multiple spatial scales in
           parallel via convolutional layers with different dilation factors.
           The activations are then combined with global scene context and
           represented as a common tensor.

        Args:
            features (tensor, float32): A 4D tensor that holds the features
                                        produced by the encoder module.
        """

        branch1 = tf.layers.conv2d(features, 256, 1,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="aspp/conv1_1")

        branch2 = tf.layers.conv2d(features, 256, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   dilation_rate=4,
                                   data_format=self._data_format,
                                   name="aspp/conv1_2")

        branch3 = tf.layers.conv2d(features, 256, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   dilation_rate=8,
                                   data_format=self._data_format,
                                   name="aspp/conv1_3")

        branch4 = tf.layers.conv2d(features, 256, 3,
                                   padding="same",
                                   activation=tf.nn.relu,
                                   dilation_rate=12,
                                   data_format=self._data_format,
                                   name="aspp/conv1_4")

        branch5 = tf.reduce_mean(features,
                                 axis=self._dims_axis,
                                 keepdims=True)

        branch5 = tf.layers.conv2d(branch5, 256, 1,
                                   padding="valid",
                                   activation=tf.nn.relu,
                                   data_format=self._data_format,
                                   name="aspp/conv1_5")

        shape = tf.shape(features)

        branch5 = self._upsample(branch5, shape, 1)

        context = tf.concat([branch1, branch2, branch3, branch4, branch5],
                            axis=self._channel_axis)

        aspp_output = tf.layers.conv2d(context, 256, 1,
                                       padding="same",
                                       activation=tf.nn.relu,
                                       data_format=self._data_format,
                                       name="aspp/conv2")
        self._output = aspp_output

    def _decoder(self, features, l2, l5, l9):
        """The decoder model applies a series of 3 upsampling blocks that each
           performs bilinear upsampling followed by a 3x3 convolution to avoid
           checkerboard artifacts in the image space. Unlike all other layers,
           the output of the model is not modified by a ReLU.

        Args:
            features (tensor, float32): A 4D tensor that holds the features
                                        produced by the ASPP module.
        """

        shape = tf.shape(features)

        layer1 = self._upsample(features, shape, 2)

        layer1 = tf.concat([l9, layer1], axis=self._channel_axis)

        layer2 = tf.layers.conv2d(layer1, 128, 3,
                                  padding="same",
                                  activation=tf.nn.relu,
                                  data_format=self._data_format,
                                  name="decoder/conv1")

        shape = tf.shape(layer2)

        layer3 = self._upsample(layer2, shape, 2)

        layer3 = tf.concat([l5, layer3], axis=self._channel_axis)

        layer4 = tf.layers.conv2d(layer3, 64, 3,
                                  padding="same",
                                  activation=tf.nn.relu,
                                  data_format=self._data_format,
                                  name="decoder/conv2")

        shape = tf.shape(layer4)

        layer5 = self._upsample(layer4, shape, 2)

        layer5 = tf.concat([l2, layer5], axis=self._channel_axis)

        layer6 = tf.layers.conv2d(layer5, 32, 3,
                                  padding="same",
                                  activation=tf.nn.relu,
                                  data_format=self._data_format,
                                  name="decoder/conv3")

        decoder_output = tf.layers.conv2d(layer6, 1, 3,
                                          padding="same",
                                          data_format=self._data_format,
                                          name="decoder/conv4")

        if self._data_format == "channels_first":
            decoder_output = tf.transpose(decoder_output, (0, 2, 3, 1))

        self._output = decoder_output

    def _upsample(self, stack, shape, factor):
        """This function resizes the input to a desired shape via the
           bilinear upsampling method.

        Args:
            stack (tensor, float32): A 4D tensor with the function input.
            shape (tensor, int32): A 1D tensor with the reference shape.
            factor (scalar, int): An integer denoting the upsampling factor.

        Returns:
            tensor, float32: A 4D tensor that holds the activations after
                             bilinear upsampling of the input.
        """

        if self._data_format == "channels_first":
            stack = tf.transpose(stack, (0, 2, 3, 1))

        stack = tf.image.resize_bilinear(stack, (shape[self._dims_axis[0]] * factor,
                                                 shape[self._dims_axis[1]] * factor))

        if self._data_format == "channels_first":
            stack = tf.transpose(stack, (0, 3, 1, 2))

        return stack

    def _normalize(self, maps, eps=1e-7):
        """This function normalizes the output values to a range
           between 0 and 1 per saliency map.

        Args:
            maps (tensor, float32): A 4D tensor that holds the model output.
            eps (scalar, float, optional): A small factor to avoid numerical
                                           instabilities. Defaults to 1e-7.
        """

        min_per_image = tf.reduce_min(maps, axis=(1, 2, 3), keep_dims=True)
        maps -= min_per_image

        max_per_image = tf.reduce_max(maps, axis=(1, 2, 3), keep_dims=True)
        maps = tf.divide(maps, eps + max_per_image, name="output")

        self._output = maps

    def _pretraining(self):
        """The first 26 variables of the model here are based on the VGG16
           network. Therefore, their names are matched to the ones of the
           pretrained VGG16 checkpoint for correct initialization.
        """

        for var in tf.global_variables()[:26]:
            #print(var)
            key = var.name.split("/", 1)[1]
            #print(key)
            if key[:2] == 'co': 
                key = key.replace("kernel:0", "weights")
                key = key.replace("bias:0", "biases")
                self._mapping[key] = var

    def forward(self, images):
        """Public method to forward RGB images through the whole network
           architecture and retrieve the resulting output.

        Args:
            images (tensor, float32): A 4D tensor that holds the values of the
                                      raw input images.

        Returns:
            tensor, float32: A 4D tensor that holds the values of the
                             predicted saliency maps.
        """

        l2, l5, l9 = self._encoder(images)
        self._aspp(self._output)
        self._decoder(self._output, l2, l5, l9)
        self._normalize(self._output)

        return self._output

    def train(self, ground_truth, predicted_maps, learning_rate):
        """Public method to define the loss function and optimization
           algorithm for training the model.

        Args:
            ground_truth (tensor, float32): A 4D tensor with the ground truth.
            predicted_maps (tensor, float32): A 4D tensor with the predictions.
            learning_rate (scalar, float): Defines the learning rate.

        Returns:
            object: The optimizer element used to train the model.
            tensor, float32: A 0D tensor that holds the averaged error.
        """

        error = loss.kld(ground_truth, predicted_maps)
        optimizer = tf.train.AdamOptimizer(learning_rate)
        optimizer = optimizer.minimize(error)

        return optimizer, error

    def save(self, saver, sess, dataset, path, device):
        """This saves a model checkpoint to disk and creates
           the folder if it doesn't exist yet.

        Args:
            saver (object): An object for saving the model.
            sess (object): The current TF training session.
            path (str): The path used for saving the model.
            device (str): Represents either "cpu" or "gpu".
        """

        os.makedirs(path, exist_ok=True)

        saver.save(sess, path + "model_%s_%s.ckpt" % (dataset, device),
                   write_meta_graph=False, write_state=False)

    def restore(self, sess, dataset, paths, device):
        """This function allows continued training from a prior checkpoint and
           training from scratch with the pretrained VGG16 weights. In case the
           dataset is either CAT2000 or MIT1003, a prior checkpoint based on
           the SALICON dataset is required.

        Args:
            sess (object): The current TF training session.
            dataset ([type]): The dataset used for training.
            paths (dict, str): A dictionary with all path elements.
            device (str): Represents either "cpu" or "gpu".

        Returns:
            object: A saver object for saving the model.
        """

        model_name = "model_%s_%s" % (dataset, device)
        salicon_name = "model_salicon_%s" % device
        vgg16_name = "vgg16_hybrid"

        ext1 = ".ckpt.data-00000-of-00001"
        ext2 = ".ckpt.index"

        saver = tf.train.Saver()

        if os.path.isfile(paths["latest"] + model_name + ext1) and \
           os.path.isfile(paths["latest"] + model_name + ext2):
            saver.restore(sess, paths["latest"] + model_name + ".ckpt")
        elif dataset in ("cat2000", "mit1003"):
            if os.path.isfile(paths["best"] + salicon_name + ext1) and \
               os.path.isfile(paths["best"] + salicon_name + ext2):
                saver.restore(sess, paths["best"] + salicon_name + ".ckpt")
            else:
                raise FileNotFoundError("Train model on SALICON first")
        else:
            if not (os.path.isfile(paths["weights"] + vgg16_name + ext1) or
                    os.path.isfile(paths["weights"] + vgg16_name + ext2)):
                download.download_pretrained_weights(paths["weights"],
                                                     "vgg16_hybrid")
            self._pretraining()
            
            loader = tf.train.Saver(self._mapping)
            loader.restore(sess, paths["weights"] + vgg16_name + ".ckpt")

        return saver

    def optimize(self, sess, dataset, path, device):
        """The best performing model is frozen, optimized for inference
           by removing unneeded training operations, and written to disk.

        Args:
            sess (object): The current TF training session.
            path (str): The path used for saving the model.
            device (str): Represents either "cpu" or "gpu".

        .. seealso:: https://bit.ly/2VBBdqQ and https://bit.ly/2W7YqBa
        """

        model_name = "model_%s_%s" % (dataset, device)
        model_path = path + model_name

        tf.train.write_graph(sess.graph.as_graph_def(),
                             path, model_name + ".pbtxt")

        freeze_graph.freeze_graph(model_path + ".pbtxt", "", False,
                                  model_path + ".ckpt", "output",
                                  "save/restore_all", "save/Const:0",
                                  model_path + ".pb", True, "")

        os.remove(model_path + ".pbtxt")

        graph_def = tf.GraphDef()

        with tf.gfile.Open(model_path + ".pb", "rb") as file:
            graph_def.ParseFromString(file.read())

        transforms = ["remove_nodes(op=Identity)",
                      "merge_duplicate_nodes",
                      "strip_unused_nodes",
                      "fold_constants(ignore_errors=true)"]

        optimized_graph_def = TransformGraph(graph_def,
                                             ["input"],
                                             ["output"],
                                             transforms)

        tf.train.write_graph(optimized_graph_def,
                             logdir=path,
                             as_text=False,
                             name=model_name + ".pb")
