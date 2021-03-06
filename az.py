import requests
import os
import json
import re
import pandas as pd
import numpy as np


class RequestData:

    def __init__(self, url):
        self.url = url

    def get_data(self):
        response = requests.get(self.url,"limit=100")
        print(response.status_code)
        print(response.content)

    def get_data_from_path(self):
        """
        :return:
        Retrieve json data from physical path and is modified according to our need
        """
        retJSON = {}
        retJSON['results'] = []
        directory = os.listdir(self.url)
        for files in directory:
            with open(self.url + "/" + files) as json_file:
                file_content = json.load(json_file)
                for result in file_content['results']:
                    route = []
                    ing = []
                    yr = None
                    month = None
                    dt = None
                    date_val = None
                    name = None
                    manufacturer_name = []
                    if 'spl_product_data_elements' in result:
                        ing = result['spl_product_data_elements']
                    if 'effective_time' in result:
                        date_val = re.match(r'(\d{4})(\d{2})(\d{2})', result['effective_time'])
                    if 'openfda' in result:
                        if 'generic_name' in result['openfda']:
                            name = ",".join(result['openfda']['generic_name'])
                        if 'route' in result['openfda']:
                            route = result['openfda']['route']
                        if 'manufacturer_name' in result['openfda']:
                            manufacturer_name = result['openfda']['manufacturer_name']
                    if date_val:
                        yr = date_val.group(1)
                        month = date_val.group(2)
                        dt = date_val.group(3)
                    json_tmp = {
                        "drug_names": name,
                        "ingredients": ing,
                        "route": route,
                        "year": yr,
                        "month": month,
                        "dt": dt,
                        "manufacturer_name": manufacturer_name
                    }
                    retJSON['results'].append(json_tmp)

        return_df = pd.DataFrame(retJSON['results'])
        return_df = self.explode(return_df, 'ingredients')
        return_df = self.explode(return_df, 'manufacturer_name')
        return_df = self.explode(return_df, 'route')

        return return_df

    def get_results(self):
        """
        Assumption each ingredient is an entry in the array
        :return:
        """
        df = self.get_data_from_path()
        # Part A
        df_A = df[['drug_names','year','manufacturer_name','ingredients']]
        res_A_tmp = df_A.groupby(['year','drug_names','manufacturer_name']).count().reset_index()
        # Result of part A
        res_A = res_A_tmp.groupby(['year','drug_names']).mean().add_prefix('avg_number_of_').reset_index()
        print(res_A)

        #Part B
        df_B = df[['route','year','ingredients']]
        res_B_tmp = df_B.groupby(['year','route','manufacturer_name']).count().reset_index()
        # Result of part B
        res_B = res_B_tmp.groupby(['year','route']).mean().add_prefix('avg_number_of_').reset_index()
        print(res_B)

    def explode(self, df, col_target):
        """
        To explode the array entries in the table into seperate rows
        :param df:
        :param col_target:
        :return: dataframe with array values exploded as rows
        """
        # Flatten columns of lists
        col_flat = [item for sublist in df[col_target] for item in sublist]
        # Row numbers to repeat
        lens = df[col_target].apply(len)
        vals = range(df.shape[0])
        ilocations = np.repeat(vals, lens)
        # Replicate rows and add flattened column of lists
        cols = [i for i, c in enumerate(df.columns) if c != col_target]
        new_df = df.iloc[ilocations, cols].copy()
        new_df[col_target] = col_flat
        return new_df

# Assumption is data is downloaded and is available in a path. The path is specified while creating object to the class
RequestData('D:/Vignesh/az').get_results()