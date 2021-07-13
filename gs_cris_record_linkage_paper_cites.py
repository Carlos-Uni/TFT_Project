import pandas as pd
import recordlinkage
from recordlinkage.preprocessing import clean
from datetime import date
import argparse

pd.options.mode.chained_assignment = None

if __name__ == '__main__':

	today = date.today()
	#check that the parameters are correct.
	def file_checker(selection, files_name):
		if selection not in files_name:
			parser.error("The file " + files_name + " is incorrect. Use the -h command to see the format and run the script correctly.")
		return files_name

	parser = argparse.ArgumentParser(description="Script that searches for articles in common between Google Scholar and accedaCRIS")
	parser.add_argument("articles_file_GS", metavar='filtered-paper-cites-GS.xlsx', 
			type=lambda s:file_checker('filtered-paper-cites-GS.xlsx', s),
	        help="File that contains the filtered articles obtained from Google Scholar")
	parser.add_argument("articles_file_CRIS", metavar='filtered-paper-cites-CRIS.xlsx', 
			type=lambda s:file_checker('filtered-paper-cites-CRIS.xlsx',s),
	        help="File that contains the filtered articles obtained from accedaCRIS")
	args = parser.parse_args()


	df_gs = pd.read_excel(args.articles_file_GS, engine="openpyxl", index_col="Art-Code")
	df_cris = pd.read_excel(args.articles_file_CRIS, engine="openpyxl", index_col="HANDLE")

	#copy of the originals dataframes to clean the data and not modify the originals
	df_gs_copy = df_gs.copy()
	df_cris_copy = df_cris.copy()
	df_gs_copy[['Article', 'Journal']] = df_gs_copy[['Article', 'Journal']].apply(lambda row: clean(row), axis=1)
	df_cris_copy[['TITLE', 'JOURNAL_TITLE']] = df_cris_copy[['TITLE', 'JOURNAL_TITLE']].apply(lambda row: clean(row), axis=1)

	#declare the indexer and use the full function
	indexer = recordlinkage.Index()
	indexer.full()

	candidates = indexer.index(df_gs_copy, df_cris_copy) #the pairs of articles to be compared
	print("Number of candidates:", len(candidates))

	#Conditions for comparison
	compare = recordlinkage.Compare()
	compare.string('Article', 'TITLE', label='TITLE')
	compare.string('Journal', 'JOURNAL_TITLE', method='jarowinkler', label='JOURNAL')
	compare.exact('Year', 'YEAR', label='YEAR')

	features = compare.compute(candidates, df_gs_copy, df_cris_copy)#dataframe with all comparisons from pairs and conditions

	#dataframe with pairs of articles that are considered equals
	matches = features[(features['TITLE'] >= 0.90) & (features['JOURNAL'] >= 0.80) & (features['YEAR'] == 1)]

	final_matches = df_gs[df_gs.index.isin(set(matches.index.get_level_values('Art-Code')))].reset_index()

	final_matches.to_excel(today.strftime("%Y-%m") + '_record_linkage_paper_cites.xlsx', index = False)