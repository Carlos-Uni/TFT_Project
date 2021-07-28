import pandas as pd
import recordlinkage
from recordlinkage.preprocessing import clean
from datetime import date
import argparse

def change_and_clean_namesGS(x):
	x['Nombre'] = x['Nombre'].lower().replace("dra.","").replace("dr.","")
	#change the order of names that contain a comma. For example: Montero Carracedo, Luis --> Luis Montero Carracedo
	if ',' in x['Nombre']:
		x['Nombre'] = x['Nombre'].split(',')[1].strip() + ' ' + x['Nombre'].split(',')[0].strip()
	return clean(x)

def dataframe_compare(df_x, df_y, id):
	#declare the indexer
	indexer = recordlinkage.Index()
	if id is True:
		indexer.full()
		#the pairs of articles to be compared
		candidates = indexer.index(df_x)
		print("The program is matching authors...")
		#Conditions for comparison
		compare = recordlinkage.Compare()
		compare.string('Nombre', 'Nombre', method='jarowinkler', label='Score')
		#dataframe with all comparisons from pairs and conditions
		features = compare.compute(candidates, df_x)
		return features[(features['Score'] >= 0.90)]
	else:
		if df_y is False:
			indexer.block('GS-Code')
			#the pairs of articles to be compared
			candidates = indexer.index(df_x)
			print("The program is filtering articles...")
		else:
			indexer.full()
			#the pairs of articles to be compared
			candidates = indexer.index(df_x, df_y)
			print("The program is matching articles...")
		#Conditions for comparison
		compare = recordlinkage.Compare()
		compare.string('Article', 'Article', label='Article')
		compare.string('Journal', 'Journal', method='jarowinkler', label='Journal')
		compare.exact('Year', 'Year', label='Year')
		if df_y is False:
			#dataframe with all comparisons from pairs and conditions
			features = compare.compute(candidates, df_x)
		else:
			#dataframe with all comparisons from pairs and conditions
			features = compare.compute(candidates, df_x, df_y)
		return features[(features['Article'] >= 0.90) & (features['Journal'] >= 0.80) & (features['Year'] == 1)]

if __name__ == '__main__':

	today = date.today()
	#check that the parameters are correct.
	def file_checker(selection, files_name):
		if selection not in files_name:
			parser.error("The file " + files_name + " is incorrect. Use the -h command to see the format and run the script correctly.")
		return files_name

	parser = argparse.ArgumentParser(description="Script that searches for duplicate authors")
	parser.add_argument("authors_file", metavar='authors-GS.csv', 
			type=lambda s:file_checker('authors-GS.csv', s),
	        help="File that contains the data of the authors obtained from Google Scholar")
	parser.add_argument("articles_file", metavar='paper-cites-GS.csv', 
			type=lambda s:file_checker('paper-cites-GS.csv',s),
	        help="File that contains the articles obtained from Google Scholar")
	args = parser.parse_args()

	df_authors = pd.read_csv(args.authors_file, skipinitialspace=True, index_col="GS-Code")
	df_arts = pd.read_csv(args.articles_file, skipinitialspace=True, index_col="Art-Code")

	#copy of the original dataframes to clean the data and not modify the originals
	df_authors_copy = df_authors.copy()
	df_arts_copy = df_arts.copy()
	df_authors_copy['Nombre'] = df_authors_copy[['Nombre']].apply(lambda row: change_and_clean_namesGS(row), axis=1)
	df_arts_copy[['Article', 'Journal']] = df_arts_copy[['Article', 'Journal']].apply(lambda row: clean(row), axis=1)

	#dataframe with all authors that may be repeated
	author_matches = dataframe_compare(df_authors_copy,False,True)

	for author_matches_index in author_matches.index:
		print("The program is matching " + df_authors.loc[author_matches_index[0], 'Nombre'] + " with " + df_authors.loc[author_matches_index[1], 'Nombre'])
		
		author_duplicate_list = []
		#dataframe with all the articles of both authors
		df_arts_compare = df_arts_copy[(df_arts_copy['GS-Code'] == author_matches_index[0]) | (df_arts_copy['GS-Code'] == author_matches_index[1])]
		#dataframe with unduplicated articles
		arts_matches = dataframe_compare(df_arts_compare, False, False)
		df_arts_compare = df_arts_compare[~df_arts_compare.index.isin(arts_matches.index.get_level_values('Art-Code_2'))]
		#the filtered articles are separated by authors
		df_arts_filtered = df_arts_compare[(df_arts_compare['GS-Code'] == author_matches_index[0])]
		df_arts_filtered2 = df_arts_compare[(df_arts_compare['GS-Code'] == author_matches_index[1])]
		#the smallest dataframe is checked and the 80% of its size is obtained.
		if len(df_arts_filtered) >= len(df_arts_filtered2):
			percentage_size = round(len(df_arts_filtered2)*(80/100))
		else:
			percentage_size = round(len(df_arts_filtered)*(80/100))

		#dataframe with the articles that the authors have in common
		arts_filtered_matches = dataframe_compare(df_arts_filtered, df_arts_filtered2, False)
		#when the number of articles that the authors have in common is equal to or more than 80%, the two authors are considered to be the same.
		if len(arts_filtered_matches) >= percentage_size:
			if df_authors.loc[author_matches_index[0], 'Citas'] >= df_authors.loc[author_matches_index[1], 'Citas']:
				author_duplicate_list.append(author_matches_index[1])
			elif df_authors.loc[author_matches_index[0], 'Citas'] < df_authors.loc[author_matches_index[1], 'Citas']:
				author_duplicate_list.append(author_matches_index[0])
			print(df_authors.loc[author_matches_index[0], 'Nombre'] + " and " + df_authors.loc[author_matches_index[1], 'Nombre'] + 
				" are the same person, so " + df_authors.loc[author_duplicate_list[0], 'Nombre'] + " is eliminated because he has fewer citations.")
			#authors and articles are removed from the original dataframes
			df_authors = df_authors[~df_authors.index.isin(author_duplicate_list)]
			df_arts = df_arts[(df_arts['GS-Code'] != author_duplicate_list[0])]

		else:
			print(df_authors.loc[author_matches_index[0], 'Nombre'] + " and " + df_authors.loc[author_matches_index[1], 'Nombre'] + 
				" aren't the same person") 

	df_authors = df_authors.reset_index()
	df_arts = df_arts.reset_index()
	df_authors.to_csv(args.authors_file, index = False)
	df_arts.to_csv(args.articles_file, index = False)