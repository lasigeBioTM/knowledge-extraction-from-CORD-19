import sys
import os
import json
import multiprocessing
from collections import Counter
from itertools import chain
import spacy
import merpy

# nlp = spacy.load("en_core_sci_lg")
nlp_craft = spacy.load("en_ner_craft_md")
nlp_cdr = spacy.load("en_ner_bc5cdr_md")
# nlp = spacy.load("en_ner_bionlp13cg_md")

# map each entity to URI using merpy
normalization_dic = {"taxon": {}, "chebi": {}, "go": {}, "do": {}}


def map_to_ontology(entity_text, ontology):
    """
    Run merpy on an entity string to get ontology URI
    """
    if entity_text in normalization_dic[ontology]:
        return normalization_dic[ontology][entity_text]
    else:
        matches = merpy.get_entities(entity_text, ontology)
        if len(matches) > 1:
            print(entity_text, ontology, matches)
        if len(matches) == 0 or len(matches[-1]) < 4:
            print("no matches", entity_text, ontology, matches)
            normalization_dic[ontology][entity_text] = entity_text
            return entity_text
        else:  # get the last match (or biggest TODO)
            best_match = matches[-1][3]
            normalization_dic[ontology][entity_text] = best_match
        return best_match


def process_multiple_docs_spacy(docs):
    """
    Run the CRAFT and CDR models on the documents
    """
    # create one empty list for each doc
    doc_dict = {i: d for i, d in enumerate(docs)}
    output_entities = [[]] * len(docs)
    doc_results = []
    for idoc, doc in enumerate(nlp_craft.pipe(docs, disable=["tagger", "parser"])):
        # doc_entities = merpy.get_entities_mp(doc_dict, lex, n_cores=10)
        # print(lex, entities)
        for ent in doc.ents:
            # output_entities[idoc].append(entity)
            # print(ent.text, ent.start_char, ent.end_char, ent.label_)
            entity_uri = ent.text
            if ent.label_ in ["CHEBI", "GO", "TAXON"]:
                entity_uri = map_to_ontology(ent.text, ent.label_.lower())
            entity = [ent.start_char, ent.end_char, ent.text, entity_uri]
            output_entities[idoc].append(entity)

    for idoc, doc in enumerate(nlp_cdr.pipe(docs, disable=["tagger", "parser"])):
        # doc_entities = merpy.get_entities_mp(doc_dict, lex, n_cores=10)
        # print(lex, entities)
        for ent in doc.ents:
            # output_entities[idoc].append(entity)
            # print(ent.text, ent.start_char, ent.end_char, ent.label_)
            entity_uri = ent.text
            if ent.label_ == "DISEASE":
                entity_uri = map_to_ontology(ent.text, "do")
                entity = [ent.start_char, ent.end_char, ent.text, entity_uri]
                output_entities[idoc].append(entity)
    # for i in range(len(output_entities)):
    #    output_entities[i] = sorted(output_entities[i])
    return output_entities


def process_doc(doc_file, output_dir):
    with open(doc_file, "r") as f_in:
        doc = json.load(f_in)
    new_doc = {
        "id": doc["paper_id"],
        "entities": {},
        "sections": {"title": [], "abstract": [], "body": [], "captions": []},
    }

    # iterate through title, abtract and section
    title = doc["metadata"]["title"]
    # print(title)
    new_doc["sections"]["title"] = process_multiple_docs_spacy([title])
    new_doc["sections"]["title"] = new_doc["sections"]["title"][0]

    abstract = [p["text"] for p in doc["abstract"]]
    # print(abstract)
    new_doc["sections"]["abstract"] = process_multiple_docs_spacy(abstract)

    body = [p["text"] for p in doc["body_text"]]
    # print(abstract)
    new_doc["sections"]["body"] = process_multiple_docs_spacy(body)

    # ref_entries includes figures and tables
    captions = [doc["ref_entries"][p]["text"] for p in doc["ref_entries"]]
    # print(abstract)
    new_doc["sections"]["captions"] = process_multiple_docs_spacy(captions)

    # count all URI
    # print(new_doc["sections"]["title"])
    all_uris = [e[3] for e in new_doc["sections"]["title"] if len(e) > 3]
    all_uris += [
        e[3] for e in chain.from_iterable(new_doc["sections"]["abstract"]) if len(e) > 3
    ]
    all_uris += [
        e[3] for e in chain.from_iterable(new_doc["sections"]["body"]) if len(e) > 3
    ]
    all_uris += [
        e[3] for e in chain.from_iterable(new_doc["sections"]["captions"]) if len(e) > 3
    ]

    # get counter of URIs and sort by value
    doc_counter = Counter(all_uris)
    new_doc["entities"] = {
        k: v
        for k, v in sorted(doc_counter.items(), key=lambda item: item[1], reverse=True)
    }

    """entities_by_uri = {} # sort by ontology
    for e in new_doc["entities"].items():
        ontology = e[0].split("/")[-1].split("_")[0]
        if ontology not in entities_by_uri:
            entities_by_uri[ontology] = []
        entities_by_uri.append(e)
    new_doc["entities"] = entities_by_uri[:]"""
    print("top doc", doc_counter.most_common(10))
    with open(
        output_dir + doc_file.split("/")[-1].split(".")[0] + "_entities.json", "w"
    ) as f_out:
        json.dump(new_doc, f_out, indent=4)
    return doc_counter


input_dir = sys.argv[1]
output_dir = sys.argv[1].rstrip("/") + "_scispacy/"
# output_dir = "/home/alamurias/covid19/comm_subset_50/"

global_entities = Counter()

all_docs = [input_dir + "/" + d for d in os.listdir(input_dir)]

print("processing docs", len(all_docs))
for d in all_docs:
    doc_entities = process_doc(d, output_dir)

    # for entities in doc_entities:
    global_entities.update(doc_entities)


print()
print("global top", global_entities.most_common(10))
print("total", sum(global_entities.values()))
