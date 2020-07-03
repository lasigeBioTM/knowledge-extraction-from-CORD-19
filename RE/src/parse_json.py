import os
import time
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from multiprocessing import Process
from blacklist import chebi_blacklist, go_blacklist, hp_blacklist, doid_blacklist


#### TYPES ANNOTATIONS ####

dict_allowed_types = {'CHEBI': 'chemical', 'GO': 'gene_function', 'HP': 'phenotype', 'DOID': 'disease'}


#### CREATE XML FILES ####

def prettify(elem):
    """Return a pretty-printed XML string for the Element

    :param elem:
    :return:
    """

    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)

    return reparsed.toprettyxml(indent='  ')


def json_text_to_list(corpus_path, filename):
    """

    :param corpus_path:
    :param filename:
    :return:
    """

    chunks = []
    with open(corpus_path + filename) as json_file:
        data = json.load(json_file)
        for part in data:
            if part == 'metadata':
                chunks.append(data[part]['title'])

            elif part == 'abstract':
                for element in data[part]:
                    if 'text' in element:
                        chunks.append(element['text'])

            elif part == 'body_text':
                for element in data[part]:
                    if 'text' in element:
                        chunks.append(element['text'])

    return chunks

#json_text_to_list('data/comm_subset_100/','007bf75961da42a7e0cc8e2855e5c208a5ec65c1.json')

def json_annotations_to_list(annotations_path, filename):
    """

    :param annotations_path:
    :param filename:
    :return:
    """

    chunks_annotations = []
    chunk_annotation_number = 0
    with open(annotations_path + filename.split('.json')[0] + '_entities.json') as json_file:
        data = json.load(json_file)
        for part in data:
            if part == 'sections':
                for element in data[part]['title']:
                    chunks_annotations.append([chunk_annotation_number, element])
                chunk_annotation_number += 1

                flat_abstract_list = [item for sublist in data[part]['abstract'] for item in sublist]
                for element in flat_abstract_list:
                    chunks_annotations.append([chunk_annotation_number, element])
                chunk_annotation_number += 1

                for element in data[part]['body']:
                    for sub_element in element:
                        chunks_annotations.append([chunk_annotation_number, sub_element])
                    chunk_annotation_number += 1

    return chunks_annotations

#json_annotations_to_list('data/comm_subset_100_entities/','007bf75961da42a7e0cc8e2855e5c208a5ec65c1.json')

def xml_file(corpus_path, annotations_path, destination_path, filename):
    """Process to create each file

    :param corpus_path:
    :param annotations_path:
    :param destination_path:
    :param filename: file name
    """

    chunks = json_text_to_list(corpus_path, filename)
    chunks_annotations = json_annotations_to_list(annotations_path, filename)

    # if len(chunks) != len(chunks_annotations):
    #     return 'Something is wrong in file', filename

    root = ET.Element('document', id = filename.split('.')[0])

    chunk_number = 0

    for chunk in chunks:

        entity_number = 0
        entities_chunk = []
        same_entities = {}
        doc = ET.SubElement(root, 'chunk', id = filename.split('.')[0] + '.c' + str(chunk_number), text = chunks[chunk_number])

        for annotation_element in chunks_annotations:

            if annotation_element[1][2] not in chebi_blacklist and annotation_element[1][2] not in go_blacklist and annotation_element[1][2] not in hp_blacklist and annotation_element[1][2] not in doid_blacklist:
                if chunk_number == annotation_element[0] and annotation_element[1][3].split('/')[-1].split('_')[0] in dict_allowed_types:

                    ET.SubElement(doc, 'entity', id=filename.split('.')[0] + '.c' + str(chunk_number) + '.e' + str(entity_number),
                                  charOffset = str(annotation_element[1][0]) + '-' + str(annotation_element[1][1]), type = dict_allowed_types[annotation_element[1][3].split('/')[-1].split('_')[0]],
                                  text = annotation_element[1][2], ontology_id = annotation_element[1][3].split('/')[-1])

                    entities_chunk.append(filename.split('.')[0] + '.c' + str(chunk_number) + '.e' + str(entity_number))
                    same_entities[filename.split('.')[0] + '.c' + str(chunk_number) + '.e' + str(entity_number)] = annotation_element[1][2]
                    entity_number += 1

        if entity_number >= 1:

            pair_number = 0

            for i in range(len(entities_chunk)):
                for j in range(i + 1, len(entities_chunk)):

                    if same_entities[entities_chunk[i]] == same_entities[entities_chunk[j]]:
                        pass
                    else:
                        ET.SubElement(doc, 'pair', id = filename.split('.')[0] + '.c' + str(chunk_number) + '.p' + str(pair_number),
                                      e1 = entities_chunk[i], e2 = entities_chunk[j], relation = 'true')

                        pair_number += 1

        chunk_number += 1

    output_file = open(destination_path + filename.split('.')[0] + '.xml', 'w', encoding = 'utf-8')
    # output_file.write('<?xml version="1.0" encoding="UTF-8"?>')
    output_file.write(prettify(root))
    output_file.close()

    return

#print(xml_file('corpora/original_text_10/', 'corpora/original_text_entities_10/', 'corpora/', 'fed39ba33ece570bf3f7e8879cf448bf93cd069e.json'))

def txt_file(corpus_path, annotations_path, destination_path, filename):
    """Process to create each file

    :param corpus_path:
    :param annotations_path:
    :param destination_path:
    :param filename: file name
    """

    chunks = json_text_to_list(corpus_path, filename)
    chunks_annotations = json_annotations_to_list(annotations_path, filename)

    # if len(chunks) != len(chunks_annotations):
    #     return 'Something is wrong in file', filename

    txt_file = open(destination_path + filename.split('.')[0] + '.txt', 'w')

    chunk_number = 0

    for chunk in chunks:

        entity_number = 0
        entities_chunk = []
        same_entities = {}

        txt_file.write(str(chunk_number) + '|' + 'chunk' + '|' + chunks[chunk_number] + '\n')

        for annotation_element in chunks_annotations:

            if annotation_element[1][2] not in chebi_blacklist and annotation_element[1][2] not in go_blacklist and annotation_element[1][2] not in hp_blacklist and annotation_element[1][2] not in doid_blacklist:
                if chunk_number == annotation_element[0] and annotation_element[1][3].split('/')[-1].split('_')[0] in dict_allowed_types:

                    txt_file.write(str(chunk_number) + '\t' + str(annotation_element[1][0])
                                   + '\t' + str(annotation_element[1][1]) + ' ' + annotation_element[1][2] + '\t' +
                                   dict_allowed_types[annotation_element[1][3].split('/')[-1].split('_')[0]].capitalize() + '\t' +
                                   annotation_element[1][3].split('/')[-1] + '\n')

                    entities_chunk.append(filename.split('.')[0] + '.c' + str(chunk_number) + '.e' + str(entity_number))
                    same_entities[filename.split('.')[0] + '.c' + str(chunk_number) + '.e' + str(entity_number)] = annotation_element[1][3].split('/')[-1]
                    entity_number += 1

        if entity_number >= 1:

            pair_number = 0
            save_pairs = []
            for i in range(len(entities_chunk)):
                for j in range(i + 1, len(entities_chunk)):

                    if same_entities[entities_chunk[i]] == same_entities[entities_chunk[j]]:
                        pass
                    elif (same_entities[entities_chunk[i]], same_entities[entities_chunk[j]]) not in save_pairs and (same_entities[entities_chunk[j]], same_entities[entities_chunk[i]]) not in save_pairs:
                        txt_file.write(str(chunk_number) + '\t' + same_entities[entities_chunk[i]].split('_')[0] +
                                       '-' + same_entities[entities_chunk[j]].split('_')[0] + '\t'
                                       + same_entities[entities_chunk[i]] + '\t' + same_entities[entities_chunk[j]] + '\n')
                        save_pairs.append((same_entities[entities_chunk[i]], same_entities[entities_chunk[j]]))
                        pair_number += 1

        chunk_number += 1
        txt_file.write('\n')

    txt_file.close()

    return

def converter(corpus_path, annotations_path, destination_path):
    """

    :param corpus_path:
    :param annotations_path:
    :param destination_path:
    """

    os.system('rm -rf ' + destination_path + '* || true')
    for (dir_path, dir_names, file_names) in os.walk(corpus_path):
        for filename in file_names:
            p = Process(target=xml_file, args=(corpus_path, annotations_path, destination_path, filename,))
            p.start()
            p.join()

            u = Process(target=txt_file, args=(corpus_path, annotations_path, 'corpora/original_text_txt_10/', filename,))
            u.start()
            u.join()
    return


#### RUN ####

def main():
    """Creates an xml file for each abstract + annotations file
    """

    converter('corpora/original_text_10/', 'corpora/original_text_entities_10/', 'corpora/original_text_xml_10/')

    return


# python3 src/parser_xml.py
if __name__ == "__main__":
    main()