import pandas as pd
from datetime import date
import argparse

if __name__ == '__main__':

	today = date.today()
	#check that the parameters are correct.
	def file_checker(selection, files_name):
		if selection not in files_name:
			parser.error("The file " + files_name + " is incorrect. Use the -h command to see the format and run the script correctly.")
		return files_name

	parser = argparse.ArgumentParser(description="Script that generates the train and test set")
	parser.add_argument("articles_belong_file", metavar='record_linkage_paper_cites.xlsx',
			type=lambda s:file_checker('record_linkage_paper_cites.xlsx', s),
	        help="File that contains Google Scholar articles from the university found in accedaCRIS")
	parser.add_argument("articles_notbelong_file", metavar='train_other_uni_paper_cites.csv', 
			type=lambda s:file_checker('train_other_uni_paper_cites.csv',s),
	        help="File that contains Google Scholar articles from other universities to create the train set")
	parser.add_argument("articles_notbelong_file2", metavar='test_other_uni_paper_cites.csv', 
			type=lambda s:file_checker('test_other_uni_paper_cites.csv',s),
	        help="File that contains Google Scholar articles from other universities to create the test set")
	args = parser.parse_args()


	#column Label is added to the articles that belong to the university
	record_linkage_df = pd.read_excel(args.articles_belong_file, engine="openpyxl")
	record_linkage_df['Label'] = 1

	#column Label is added to the articles that don't belong to the university.
	foreign_art = pd.read_csv(args.articles_notbelong_file, skipinitialspace=True)
	foreign_art['Label'] = 0
	foreign_other_art = pd.read_csv(args.articles_notbelong_file2, skipinitialspace=True)
	foreign_other_art['Label'] = 0
	foreign_other_art = foreign_other_art.head(len(record_linkage_df))

	#the dataframes are combined to obtain the test and training set
	train_data = pd.concat([record_linkage_df, foreign_art])
	test_data = pd.concat([record_linkage_df, foreign_other_art])

	#shuffle dataframes content
	train_data = train_data.sample(frac=1, random_state=1)
	test_data = test_data.sample(frac=1, random_state=1)

	train_data.to_excel(today.strftime("%Y-%m") + '_train_paper_cites_GS.xlsx', index = False)
	test_data.to_excel(today.strftime("%Y-%m") + '_test_paper_cites_GS.xlsx', index = False)