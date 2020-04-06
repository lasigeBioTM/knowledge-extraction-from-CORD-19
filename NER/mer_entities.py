import os
import sys
import json
import tqdm
import re
import multiprocessing
from collections import Counter
from itertools import chain

import merpy


global_entities = Counter()


def process_doc(doc_file, lexicons, output_dir):
    """
    Open one json file with one doc, run merpy with lexicons and write results to file

    """
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
    new_doc["sections"]["title"] = process_multiple_docs_lexicons_sp(
        [title], active_lexicons
    )
    new_doc["sections"]["title"] = new_doc["sections"]["title"][0]

    abstract = [p["text"] for p in doc["abstract"]]
    # print(abstract)
    new_doc["sections"]["abstract"] = process_multiple_docs_lexicons_sp(
        abstract, active_lexicons
    )

    body = [p["text"] for p in doc["body_text"]]
    # print(abstract)
    new_doc["sections"]["body"] = process_multiple_docs_lexicons_sp(
        body, active_lexicons
    )

    # ref_entries includes figures and tables
    captions = [doc["ref_entries"][p]["text"] for p in doc["ref_entries"]]
    # print(abstract)
    new_doc["sections"]["captions"] = process_multiple_docs_lexicons_sp(
        captions, active_lexicons
    )

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


def repl(m):
    # replace all matches with "a"
    return "a" * len(m.group())


def process_multiple_docs_lexicons_sp(docs, lexicons):
    """
    Iterate through list of doc directories
    """
    # create one empty list for each doc
    doc_dict = {i: d for i, d in enumerate(docs)}
    output_entities = [[]] * len(docs)
    doc_results = []
    for idoc, doc in enumerate(docs):
        if sum(map(str.isalnum, doc)) < 5:  # must have at least 5 alnum
            print("no words", doc)
            continue
        doc = re.sub(r"[^A-Za-z0-9 ]{2,}", repl, doc)
        for l in lexicons:
            doc_results += merpy.get_entities(doc, l)
        for e in doc_results:
            # doc_entities = merpy.get_entities_mp(doc_dict, lex, n_cores=10)
            # print(lex, entities)
            # for e in l_entities:
            if len(e) > 2:
                entity = [int(e[0]), int(e[1]), e[2]]
                if len(e) > 3:  # URI
                    entity.append(e[3])
                if entity not in output_entities[idoc]:
                    output_entities[idoc].append(entity)
    for i in range(len(output_entities)):
        output_entities[i] = sorted(output_entities[i])
    return output_entities


# update MER
if sys.argv[1] == "setup":
    print("download latest obo files")
    merpy.download_lexicon("http://purl.obolibrary.org/obo/doid.owl", "do", ltype="owl")
    merpy.download_lexicon("http://purl.obolibrary.org/obo/go.owl", "go", ltype="owl")
    merpy.download_lexicon("http://purl.obolibrary.org/obo/hp.owl", "hpo", ltype="owl")
    merpy.download_lexicon(
        "ftp://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl",
        "chebi",
        ltype="owl",
    )
    merpy.download_lexicon(
        "http://purl.obolibrary.org/obo/ncbitaxon.owl", "taxon", ltype="owl"
    )
    merpy.download_lexicon(
        "https://raw.githubusercontent.com/CIDO-ontology/cido/master/src/ontology/cido.owl",
        "cido",
        "owl",
    )

    print("process lexicons")
    merpy.process_lexicon("do", ltype="owl")
    merpy.process_lexicon("go", ltype="owl")
    merpy.process_lexicon("hpo", ltype="owl")
    merpy.process_lexicon("chebi", ltype="owl")
    merpy.process_lexicon("taxon", ltype="owl")
    merpy.process_lexicon("cido", "owl")

    merpy.delete_obsolete("do")
    merpy.delete_obsolete("go")
    merpy.delete_obsolete("hpo")
    merpy.delete_obsolete("chebi")
    merpy.delete_obsolete("taxon")
    merpy.delete_obsolete("cido")

    merpy.delete_entity("protein", "chebi")
    merpy.delete_entity("protein", "cido")
    merpy.delete_entity("protein", "hpo")
    merpy.delete_entity("polypeptide chain", "chebi")
    merpy.delete_entity("data", "taxon")
    merpy.delete_entity("one", "chebi")
    merpy.delete_entity_by_uri("http://purl.obolibrary.org/obo/PATO_0000070", "hpo")

else:
    active_lexicons = ["do", "go", "hpo", "chebi", "taxon", "cido"]
    # active_lexicons = ["do"]
    # TODO check if all these lexicons are preprocessed (merpy.get_lexicons[1])
    # merpy.merge_processed_lexicons(active_lexicons, "covid")
    # active_lexicons = ["covid"]
    input_dir = sys.argv[1]
    output_dir = sys.argv[1].rstrip("/") + "_entities/"
    # output_dir = "/home/alamurias/covid19/comm_subset_50/"

    print("processing docs")

    with multiprocessing.Pool(processes=10) as pool:
        doc_entities = pool.starmap(
            process_doc,
            [
                (input_dir + "/" + d, active_lexicons, output_dir)
                for d in os.listdir(input_dir)
            ],
        )
        for entities in doc_entities:
            global_entities.update(entities)

        entities_by_uri = {}

        print()
        print("global top", global_entities.most_common(10))
        print("total", sum(global_entities.values()))
