from tensorflow.keras.layers import Layer, Dense, LayerNormalization, Dropout, MultiHeadAttention
from tensorflow.keras.initializers import get as get_initializer
import tensorflow as tf


class TokenAndPositionEmbedding(Layer):
    def __init__(self, vocabulary_size, sequence_length, embedding_dim,
                 embeddings_initializer='glorot_uniform', mask_zero=False, **kwargs):
        super(TokenAndPositionEmbedding, self).__init__(**kwargs)
        self.vocabulary_size = vocabulary_size
        self.sequence_length = sequence_length
        self.embedding_dim = embedding_dim
        self.embeddings_initializer = get_initializer(embeddings_initializer)
        self.mask_zero = mask_zero
        self.token_emb = tf.keras.layers.Embedding(input_dim=vocabulary_size,
                                                   output_dim=embedding_dim,
                                                   mask_zero=mask_zero,
                                                   embeddings_initializer=self.embeddings_initializer)
        self.pos_emb = tf.keras.layers.Embedding(input_dim=sequence_length,
                                                 output_dim=embedding_dim,
                                                 embeddings_initializer=self.embeddings_initializer)

    def call(self, inputs):
        maxlen = tf.shape(inputs)[-1]
        positions = tf.range(start=0, limit=maxlen, delta=1)
        positions = self.pos_emb(positions)
        x = self.token_emb(inputs)
        return x + positions

    def get_config(self):
        config = super(TokenAndPositionEmbedding, self).get_config()
        config.update({
            'vocabulary_size': self.vocabulary_size,
            'sequence_length': self.sequence_length,
            'embedding_dim': self.embedding_dim,
            'embeddings_initializer': self.embeddings_initializer,
            'mask_zero': self.mask_zero
        })
        return config


class TransformerEncoder(Layer):
    def __init__(self, intermediate_dim, num_heads, dropout=0.2, activation="gelu",
                 layer_norm_epsilon=1e-05, kernel_initializer='glorot_uniform', bias_initializer='zeros', **kwargs):
        super(TransformerEncoder, self).__init__(**kwargs)
        self.num_heads = num_heads
        self.intermediate_dim = intermediate_dim
        self.dropout_rate = dropout
        self.activation = tf.keras.activations.get(activation)
        self.layer_norm_epsilon = layer_norm_epsilon
        self.kernel_initializer = get_initializer(kernel_initializer)
        self.bias_initializer = get_initializer(bias_initializer)

        self.attention = MultiHeadAttention(
            num_heads=num_heads, key_dim=intermediate_dim,
            kernel_initializer=self.kernel_initializer, bias_initializer=self.bias_initializer)
        self.dense_proj = Dense(intermediate_dim,
                                activation=self.activation,
                                kernel_initializer=self.kernel_initializer,
                                bias_initializer=self.bias_initializer)
        self.dropout = Dropout(dropout)
        self.layernorm1 = LayerNormalization(epsilon=layer_norm_epsilon)
        self.layernorm2 = LayerNormalization(epsilon=layer_norm_epsilon)

    def call(self, inputs, training=False):
        attn_output = self.attention(inputs, inputs)
        attn_output = self.dropout(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)

        ffn_output = self.dense_proj(out1)
        ffn_output = self.dropout(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

    def get_config(self):
        config = super(TransformerEncoder, self).get_config()
        config.update({
            'num_heads': self.num_heads,
            'intermediate_dim': self.intermediate_dim,
            'dropout_rate': self.dropout_rate,
            'activation': tf.keras.activations.serialize(self.activation),
            'layer_norm_epsilon': self.layer_norm_epsilon,
            'kernel_initializer': tf.keras.initializers.serialize(self.kernel_initializer),
            'bias_initializer': tf.keras.initializers.serialize(self.bias_initializer),
        })
        return config
