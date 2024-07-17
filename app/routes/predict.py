from flask import Blueprint
from app import chardet, os, string, urlparse, requests, tf, jwt_required, request, jsonify, Article, mongo, ObjectId, np, datetime, pytz, re, json
from transformers import AutoTokenizer, TFAutoModelForTokenClassification, pipeline

bp = Blueprint('predict', __name__)

# Defining Functions


def custom_standardization(input_data):
    lowercase = tf.strings.lower(input_data)
    stripped_html = tf.strings.regex_replace(lowercase, '<br />', ' ')
    return tf.strings.regex_replace(stripped_html, '[%s]' % re.escape(string.punctuation), '')


def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def titlefinder(s):
    words = s.split()
    return ' '.join(words[:2])


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def ner_tagging(user_input):
    ner_results = nlp(user_input)
    return ner_results


def format_ner_results(ner_results):
    formatted_results = []
    offset = 0
    for entity in ner_results:
        entity_label = label_mapping.get(
            entity['entity_group'], entity['entity_group'])
        start = entity['start'] + offset
        end = entity['end'] + offset
        formatted_results.append({
            "entity": entity_label,
            "score": float(entity["score"]),
            "word": entity["word"],
            "start": int(start),
            "end": int(end)
        })
    return formatted_results


def filter_entities(entities, entity_type):
    return [
        {"entity": entity["entity"],
            "start": entity["start"], "end": entity["end"]}
        for entity in entities if entity["entity"] == entity_type
    ]


def ner_output(string, filtered_entities):
    return [string[entity["start"]:entity["end"]] for entity in filtered_entities]


def list_to_str(sliced_strings, delimiter=", "):
    return delimiter.join(sliced_strings)


# Loading all models
model_path = 'model/transformer'
model = tf.keras.models.load_model(model_path)
tokenizer = AutoTokenizer.from_pretrained("sagorsarker/mbert-bengali-ner")
model = TFAutoModelForTokenClassification.from_pretrained(
    "sagorsarker/mbert-bengali-ner")
nlp = pipeline("ner", model=model, tokenizer=tokenizer, grouped_entities=True)
API_URL = "https://api-inference.huggingface.co/models/csebuetnlp/mT5_multilingual_XLSum"
headers = {"Authorization": f"Bearer {os.getenv('SUMMARIZER_API_TOKEN')} "}


# Load vectorization layer and vocabulary
vectorize_layer = tf.keras.layers.TextVectorization(
    standardize=custom_standardization,
    max_tokens=20000,
    output_mode='int',
    output_sequence_length=500
)
# Use raw string or double backslashes
vocab_path = r"model/vocabulary.txt"

with open(vocab_path, 'rb') as file:
    raw_data = file.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']

with open(vocab_path, 'r', encoding=encoding) as file:
    vocab = [line.strip() for line in file]
unique_vocab = list(dict.fromkeys(vocab))
vectorize_layer.set_vocabulary(unique_vocab)

# Mapping dictionaries
int_to_str = {
    0: 'দুর্ঘটনা', 1: 'বাংলাদেশ', 2: 'বাণিজ্য',
    3: 'অপরাধ', 4: 'অর্থনীতি', 5: 'শিক্ষা',
    6: 'বিনোদন', 7: 'দুর্যোগ', 8: 'আন্তর্জাতিক', 9: 'মতামত', 10: 'রাজনৈতিক', 11: 'খেলাধুলা', 12: 'Technology'
}
label_mapping = {
    "LABEL_0": "Not an entity (O)",
    "LABEL_1": "Person (PER)",
    "LABEL_2": "Organization (ORG)",
    "LABEL_3": "Location (LOC)",
    "LABEL_4": "Miscellaneous (MISC)",
    "LABEL_5": "Location (LOC)",
    "LABEL_6": "Organization (ORG)"
}


@bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    data = request.json
    if 'input' not in data:
        return jsonify({'error': 'No text provided'}),
    if is_url(data['input']):
        url = data['input']
        to_article = Article(url, language="en")
        to_article.download()
        to_article.parse()
        user_input = to_article.text
    else:
        user_input = data['input']
    # Token Validation
    # Check blacklist before processing the request
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing Authorization header'}), 401
    token = auth_header.split()[1]
    is_blacklisted = mongo.db.token_blacklist.find_one({'token': token})
    if is_blacklisted:
        return jsonify({'error': 'Token is blacklisted'}), 401
    # Input Assignment

    user_id = ObjectId(data.get('user_id'))

    # Prediction
    ############
    processed_input = custom_standardization(tf.constant([user_input]))
    vectorized_input = vectorize_layer(processed_input)
    prediction = model.predict(vectorized_input)
    predicted_class_index = np.argmax(prediction)
    prediction_output = int_to_str[predicted_class_index]

    # Summary
    #########
    summary = query(user_input)
    prediction_summary = summary[0]['summary_text']

    # Named Entity Recognition
    #########################
    ner_results = ner_tagging(user_input)
    formatted_ner_results = format_ner_results(ner_results)
    ner_json = json.dumps(formatted_ner_results, ensure_ascii=False, indent=4)
    ner_dict = json.loads(ner_json)
    # Filter for Location entities
    location_entities = filter_entities(ner_dict, "Location (LOC)")
    locations_list = ner_output(user_input, location_entities)
    locations = list_to_str(locations_list)

    # Filter for Organization entities
    org_entities = filter_entities(ner_dict, "Organization (ORG)")
    orgs_list = ner_output(user_input, org_entities)
    orgs = list_to_str(orgs_list)

    # Filter for Person entities
    person_entities = filter_entities(ner_dict, "Person (PER)")
    persons_list = ner_output(user_input, person_entities)
    persons = list_to_str(persons_list)

    # Current Time
    current_time = datetime.now(pytz.utc)
    formatted_time = current_time.strftime(
        '%Y-%m-%dT%H:%M:%S.%f')[:-3] + current_time.strftime('%z')
    formatted_time = formatted_time[:-2] + ':' + formatted_time[-2:]
    # Event Log structure
    log = {
        'corpus': user_input,
        'event': prediction_output,
        'title': titlefinder(prediction_summary),
        'summary': prediction_summary,
        'people': persons,
        'orgs': orgs,
        'locations': locations,
        'user_id': user_id,
        'created': formatted_time
    }

    mongo.db.eventlogs.insert_one(log)
    return jsonify({
        'result': prediction_output,
        'summary': prediction_summary,
        'people': persons,
        'organizations': orgs,
        'locations': locations
    })
