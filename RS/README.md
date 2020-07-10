# README #

This module creates a recommendation dataset with the format of <user,item,rating>, where users are authors from research articles, the items are biomedical entities from multi-field ontologies, and
the ratings are the number of articles an author wrote about an item. 



### Requirements: ###
* python > 3
* numpy
* configargparse
* pandas
* scipy
* sklearn
* unidecode
* unicode

### Data: ###
* Original documents: https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge 
* Entities Documents: From https://github.com/lasigeBioTM/knowledge-extraction-from-CORD-19/tree/master/NER


### Running: ###
* configure config file

````
python create_dataset.py
````

* output: csv file with user, item, rating columns

