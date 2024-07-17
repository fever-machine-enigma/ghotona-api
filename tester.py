from transformers import AutoTokenizer, TFAutoModelForTokenClassification, pipeline
import json
# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("sagorsarker/mbert-bengali-ner")
model = TFAutoModelForTokenClassification.from_pretrained(
    "sagorsarker/mbert-bengali-ner")

# Initialize the NER pipeline
nlp = pipeline("ner", model=model, tokenizer=tokenizer, grouped_entities=True)

# Mapping from LABEL_0 to LABEL_6 to human-readable labels
label_mapping = {
    "LABEL_0": "Not an entity (O)",
    "LABEL_1": "Person (PER)",
    "LABEL_2": "Organization (ORG)",
    "LABEL_3": "Location (LOC)",
    "LABEL_4": "Miscellaneous (MISC)",
    "LABEL_5": "Location (LOC)",
    "LABEL_6": "Organization (ORG)"
}


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


# Take user input
user_input = input("Enter a sentence for NER tagging: ")

# Get NER results
results = ner_tagging(user_input)

# Format and print the output
formatted_output = format_ner_results(results)
json_output = json.dumps(formatted_output, ensure_ascii=False, indent=4)
print(json_output)
