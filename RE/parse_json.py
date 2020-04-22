import os
import time
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from multiprocessing import Process


#### TYPES ANNOTATIONS ####

dict_allowed_types = {'CHEBI':'drug', 'GO':'gene_product', 'HP':'phenotype', 'DOID':'disease'}


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
        doc = ET.SubElement(root, 'chunk', id = filename.split('.')[0] + '.c' + str(chunk_number), text = chunks[chunk_number])

        for annotation_element in chunks_annotations:

            if chunk_number == annotation_element[0] and annotation_element[1][3].split('/')[-1].split('_')[0] in dict_allowed_types:

                ET.SubElement(doc, 'entity', id = filename.split('.')[0] + '.c' + str(chunk_number) + '.e' + str(entity_number),
                              charOffset = str(annotation_element[1][0]) + '-' + str(annotation_element[1][1]), type = dict_allowed_types[annotation_element[1][3].split('/')[-1].split('_')[0]],
                              text = annotation_element[1][2], ontology_id = annotation_element[1][3].split('/')[-1])

                entities_chunk.append(filename.split('.')[0] + '.c' + str(chunk_number) + '.e' + str(entity_number))
                entity_number += 1

        if entity_number >= 1:

            pair_number = 0

            for i in range(len(entities_chunk)):
                for j in range(i + 1, len(entities_chunk)):
                    ET.SubElement(doc, 'pair', id = filename.split('.')[0] + '.c' + str(chunk_number) + '.p' + str(pair_number),
                                  e1 = entities_chunk[i], e2 = entities_chunk[j], relation = 'true')

                    pair_number += 1

        chunk_number += 1

    output_file = open(destination_path + filename.split('.')[0] + '.xml', 'w', encoding = 'utf-8')
    # output_file.write('<?xml version="1.0" encoding="UTF-8"?>')
    output_file.write(prettify(root))
    output_file.close()

    return

print(xml_file('data/comm_subset_100/', 'data/comm_subset_100_entities/', 'corpora/', '007bf75961da42a7e0cc8e2855e5c208a5ec65c1.json'))

def xml_converter(corpus_path, annotations_path, destination_path):
    """

    :param corpus_path:
    :param annotations_path:
    :param destination_path:
    """

    os.system('rm -rf ' + destination_path + '* || true')
    for (dir_path, dir_names, file_names) in os.walk(annotations_path):
        for filename in file_names:
            p = Process(target=xml_file, args=(corpus_path, annotations_path, destination_path, filename,))
            p.start()
            p.join()

    return


#### RUN ####

# def main():
#     """Creates an xml file for each abstract + annotations file
#     """
#
#     xml_converter('corpora/divided_by_sentences_corpus/', 'corpora/annotations/', 'corpora/xml_corpus/')
#
#     return
#
#
# # python3 src/parser_xml.py
# if __name__ == "__main__":
#     main()