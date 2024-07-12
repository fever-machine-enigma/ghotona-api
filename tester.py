import tensorflow as tf
from tf_keras.models import load_model

model_path = 'model/transformer.h5'

model = load_model(model_path)

print(model)
