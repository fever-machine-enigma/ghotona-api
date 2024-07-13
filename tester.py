import tensorflow as tf
import numpy as np

print(tf.__version__)

# Load vocabulary
vocab_path = 'model/vocabulary.txt'
with open(vocab_path, 'r', encoding='utf-8') as f:
    vocab_list = [line.strip() for line in f]

# Create a word to index dictionary
word_index = {word: idx for idx, word in enumerate(vocab_list)}

# Function to preprocess a single article


def preprocess_article(article_text, word_index, max_length=500):
    # Tokenize and vectorize article text
    vectorized_sentence = [word_index.get(
        word, len(vocab_list) - 1) for word in article_text.split()]

    # Pad sequence to max_length
    padded_sentence = tf.keras.preprocessing.sequence.pad_sequences(
        [vectorized_sentence], maxlen=max_length, padding='post', truncating='post')

    return padded_sentence


# Load your trained model
lstm_model_path = 'transformer_saved'
lstm_model = tf.keras.models.load_model(lstm_model_path)

# Function to get user input and classify


def classify_article():
    article_text = input("Enter the article text (in Bengali): ")
    preprocessed_article = preprocess_article(article_text, word_index)
    predictions = lstm_model.predict(preprocessed_article)
    class_labels = ['দুর্ঘটনা', 'বাংলাদেশ', 'বাণিজ্য', 'অপরাধ', 'অর্থনীতি', 'শিক্ষা',
                    'বিনোদন', 'দুর্যোগ', 'আন্তর্জাতিক', 'মতামত', 'রাজনৈতিক', 'খেলাধুলা', 'Technology']
    predicted_label = class_labels[np.argmax(predictions)]
    print("Predicted Label:", predicted_label)


# Call the function to classify user input
classify_article()
