import pandas as pd
import recordlinkage
from recordlinkage.preprocessing import clean
import numpy as np
from datetime import date
import argparse

if __name__ == '__main__':

	today = date.today()
	#check that the parameters are correct.
	def file_checker(file_name):
		if "paper_cites_CRIS.xlsx" not in file_name:
			parser.error("The file " + file_name + " is incorrect. Use the -h command to see the format and run the script correctly.")
		return file_name

	parser = argparse.ArgumentParser(description="Script that filters accedaCRIS articles")
	parser.add_argument("articles_file", metavar='paper_cites_CRIS.xlsx', type=lambda s:file_checker(s),
	            help="File that contains the articles obtained from accedaCRIS")
	args = parser.parse_args()

	df = pd.read_excel(args.articles_file, engine="openpyxl")

	#the -1 are deleted from the original
	df = df.loc[:, 'TITLE':'AUTHOR_CODES'].apply(lambda row: row.replace("-1", np.nan), axis=1)

	#copy of the original dataframe to clean the data and not modify the original one
	df_copy = df.copy()
	df_copy[['TITLE', 'ISSN','JOURNAL_TITLE', 'AUTHOR_LIST']] = df_copy[['TITLE', 'ISSN', 'JOURNAL_TITLE', 'AUTHOR_LIST']].apply(lambda row: clean(row, remove_brackets=False), axis=1)
	df_copy['COUNT'] = df_copy.count(axis=1)#column is added with the number of fields that are not empty
	df_copy = df_copy.sort_values(by=['AUTHOR_CODES','AUTHOR_NAME','COUNT'], na_position='first')

	#declare the indexer and use the full function
	indexer = recordlinkage.Index()
	indexer.full()

	candidates = indexer.index(df_copy)#the pairs of articles to be compared
	print("Number of candidates:", len(candidates))

	#Conditions for comparison
	compare = recordlinkage.Compare()
	compare.string('TITLE', 'TITLE', threshold=0.90, label='TITLE')
	compare.string('AUTHOR_LIST', 'AUTHOR_LIST', method='jarowinkler', threshold=0.80, label='AUTHOR_LIST')
	compare.string('JOURNAL_TITLE', 'JOURNAL_TITLE', method='jarowinkler', threshold=0.85, label='JOURNAL_TITLE')
	compare.exact('ISSN', 'ISSN', label='ISSN')
	compare.exact('DOI', 'YEAR', label='DOI')
	compare.exact('YEAR', 'YEAR', label='YEAR')

	features = compare.compute(candidates, df_copy) #dataframe with all comparisons from pairs and conditions
	features = features.rename_axis(['HANDLE_1','HANDLE_2']) #indexes are renamed to understand them better

	#dataframe with pairs of articles that are considered duplicate
	matches = features[(features.sum(axis=1) >= 3) & (features['TITLE'] == 1)]

	unique_art = df[~df.index.isin(matches.index.get_level_values('HANDLE_2'))] #dataframe with unique articles

	#author codes of duplicated articles are added to unique articles
	def group_author_codes(row):
		strAuth = row['AUTHOR_CODES']
		same_matches = matches.loc[(matches.index.get_level_values('HANDLE_1') == row.name)]
		for indexes in same_matches.index:
			if df_copy.loc[indexes[1], 'AUTHOR_CODES'] not in strAuth:
				strAuth += "," + df_copy.loc[indexes[1], 'AUTHOR_CODES']
		row['AUTHOR_CODES'] = strAuth
		return row

	df_cris = unique_art.apply(lambda row: group_author_codes(row), axis=1)

	df_cris.to_excel(today.strftime("%Y-%m") + '_filtered-paper-cites-CRIS.xlsx', index = False)
	