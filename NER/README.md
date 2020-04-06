# NER for CORD19

This module extracts and normalizes entities from the CORD19 dataset.
It opens each json file and runs NER on the title, abstract, body text and captions,
according to the segmentations provided on the original corpus.

Two NER options were explored:

## MER using merpy interface

The *mer_entities.py* has one argument which could be *setup* to downloaded and process
the following lexicons: ["do", "go", "hpo", "chebi", "taxon", "cido"]

````
python mer_entities.py setup
````

or a directory (dirname) to process the json files on that directory and output 
to dirname_entities:

````
python mer_entities.py dirname
````

## Spacy with CRAFT and CDR model

We also applied the CRAFT and CDR models trained has part of [scispacy](https://allenai.github.io/scispacy/).
Then we run MER on each entity string to obtain the URI of chemicals, diseases and species ["do", "go", "chebi", "taxon"]

````
python scispacy_entities.py dirname
````

## Output format

Both scripts have the same output, which is a json file for each document with the following structure:
{id,
 entities: {uri: doc_count},
 sections: {section_name:
            [
              [start_index, end_index, entity_string, entity_uri]}
            ]
}

Every section except title will have multiple paragraphs, so the value of its dictionary is a list of lists.
Using the scispacy script, if the entity was not normalized, the URI will be the same as the entity string.