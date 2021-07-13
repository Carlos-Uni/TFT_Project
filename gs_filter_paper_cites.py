import pandas as pd
import recordlinkage
from recordlinkage.preprocessing import clean
from datetime import date
import argparse


if __name__ == '__main__':

	today = date.today()
	#check that the parameters are correct.
	def file_checker(file_name):
		if "paper-cites-GS.csv" not in file_name:
			parser.error("The file " + file_name + " is incorrect. Use the -h command to see the format and run the script correctly.")
		return file_name

	parser = argparse.ArgumentParser(description="Script that filters Google Scholar articles")
	parser.add_argument("articles_file", metavar='paper-cites-GS.csv', type=lambda s:file_checker(s),
	            help="File that contains the articles obtained from Google Scholar")
	args = parser.parse_args()

	df = pd.read_csv(args.articles_file, skipinitialspace=True, index_col="Art-Code")

	#copy of the original dataframe to clean the data and not modify the original one
	df_copy = df.copy()
	df_copy[['Article', 'Journal']] = df_copy[['Article', 'Journal']].apply(lambda row: clean(row), axis=1)
	df_copy = df_copy.sort_values(by=['Cites'], na_position='first')

	#declare the indexer and use the full function
	indexer = recordlinkage.Index()
	indexer.full()

	candidates = indexer.index(df_copy) #the pairs of articles to be compared
	print("Number of candidates:", len(candidates))

	#Conditions for comparison
	compare = recordlinkage.Compare()
	compare.string('Article', 'Article', label='Article')
	compare.string('Journal', 'Journal', method='jarowinkler', label='Journal')
	compare.exact('Year', 'Year', label='Year')

	features = compare.compute(candidates, df_copy) #dataframe with all comparisons from pairs and conditions

	#dataframe with pairs of articles that are considered special
	special_matches = features[(features['Article'] >= 0.90) & ((features['Journal'] < 0.80) | (features['Year'] != 1))]
	features = features[~features.index.isin(special_matches.index)]

	matches = features[(features['Article'] >= 0.90)] #dataframe with pairs of articles that are considered duplicate

	#select special items considering the number of citations
	def select_special_articles(row):
		if df.loc[row.name[0], 'Cites'] <= df.loc[row.name[1], 'Cites']:
			special_matches_list.add(row.name[0])
		else:
			special_matches_list.add(row.name[1])

	special_matches_list = set()
	special_matches.apply(lambda row: select_special_articles(row), axis=1)

	#dataframe with unique articles
	unique_art = df[~df.index.isin(matches.index.get_level_values('Art-Code_2')) &
	 ~df.index.isin(special_matches_list)].reset_index()

	#author codes of duplicated articles are added to unique articles and articles removed because of duplication are added to a list
	def group_author_codes(row):
		strAuth = row['GS-Code']
		same_matches = matches.loc[(matches.index.get_level_values('Art-Code_1') == row['Art-Code'])]
		for indexes in same_matches.index:
			repeated_articles_list.add(indexes[1])
			if df.loc[indexes[1], 'GS-Code'] not in strAuth:
				strAuth += "," + df.loc[indexes[1], 'GS-Code']
		row['GS-Code'] = strAuth
		return row

	repeated_articles_list = set()

	unique_art = unique_art.apply(lambda row: group_author_codes(row), axis=1)
	#dataframe with the codes of the special articles
	special_art = pd.DataFrame(special_matches.index.values.tolist(), columns =['Art-Code_1', 'Art-Code_2'])
	#articles that have been deleted because of duplicates, are removed from special dataframe
	special_art = special_art[~special_art['Art-Code_1'].isin(repeated_articles_list) & 
	 ~special_art['Art-Code_2'].isin(repeated_articles_list)]

	unique_art.to_excel(today.strftime("%Y-%m") + '_filtered-paper-cites-GS.xlsx', index = False)
	special_art.to_excel(today.strftime("%Y-%m") + '_special-paper-cites-GS.xlsx', index = False)
