import pandas as pd
import configargparse
from data import *
import sys
import json
from functions import *
import numpy as np
import unidecode



pd.set_option('display.max_columns', None)
pd.set_option("max_rows", None)





if __name__ == '__main__':

    p = configargparse.ArgParser(default_config_files=['../config/config.ini'])
    p.add('-mc', '--my-config', is_config_file=True, help='alternative config file path')

    p.add("-oj", "--path_to_original_json_folder", required=False, help="path to original json", type=str)
    p.add("-ej", "--path_to_entities_json_folder", required=False, help="path to entities json", type=str)
    p.add("-pathcsv", "--path_to_csv", required=False, help="path to final csv", type=str)

    options = p.parse_args()

    original_json_folder = options.path_to_original_json_folder
    entities_json_folder = options.path_to_entities_json_folder

    path_to_final_csv = options.path_to_csv

    entities_list_of_json_files = list_files_in_directory(entities_json_folder)

    user_item_rating_all = []

    count = 0

    for file in entities_list_of_json_files:
        print(count, "-", len(entities_list_of_json_files))


        j_file_entities = open_json_file_pd(entities_json_folder, file)

        df_entities = get_entities_id(get_entities(j_file_entities))

        article_id = get_article_id(j_file_entities)

        j_file_original = open_json_file(original_json_folder, article_id)

        list_of_authors = get_authors_names(j_file_original)

        user_item_rating = get_user_item_rating(list_of_authors, df_entities)

        user_item_rating_all.append(user_item_rating)


        count+=1

    flat_list = []
    for sublist in user_item_rating_all:
        for item in sublist:
            flat_list.append(item)



    array = np.array(flat_list)

    final_data = pd.DataFrame(array,  columns=['user', 'item', 'rating'])

    sum_df = final_data.groupby(['user', 'item']).size().reset_index().rename(columns={0: 'rating'})

    sum_df.to_csv(path_to_final_csv, index=False, header=False)













