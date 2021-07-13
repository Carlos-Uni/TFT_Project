# Summary
The present proyect aims to help universities obtain academic articles from Google Scholar 
and to determine, using Machine Learning techniques, if the articles belong to the university or 
not, in order to enable their upload.
For this purpose, a system have been develop to facilitate the download of academic articles 
from the Google Scholar platafform, and since articles might be duplicated, different algorithms 
are used to filter them.Next, the articles filtered from Google Scholar are matched with the articles filtered from accedaCRIS(or any other university) obtaining a set of articles that we know belong to the university.
Finally, a simple neural network has been created using the Keras library, which can 
determine if the articles correspond to the university with a reliability of 80%

# Content
The project consists of nine scripts:

-**gs_author_statistics:** This script obtains author data from Google Scholar and generate ***authors-GS.csv*** file. You need to indicate the code that Google Scholar uses to group the authors to an university and the URL of the search for authors associated to the university.

-**gs_paper_cites:** This script obtains from Google Schoolar the articles associated to the authors listed in ***authors-GS.csv*** and generate ***paper-cites-GS.csv*** file.

-**gs_author_compare:** This script searches for duplicate authors by comparing their names and articles using ***authors-GS.csv*** and ***paper-cites-GS.csv*** files. When an author is considered a duplicate it is removed from ***authors-GS.csv*** and ***paper-cites-GS.csv***.

-**gs_filter_paper_cites:** Script that filters the Google Scholar articles found in paper-cites-GS.csv using algorithms for string similarity and generates the file ***filtered-paper-cites-GS.xlsx***.

-**cris_filter_paper_cites** Script that filters the accedaCRIS(or any other university) articles using algorithms for string similarity and generates the file ***filtered-paper-cites-CRIS.xlsx***. Remember to change the names of the columns if you want to use this script in the articles of your university

-**gs_cris_record_linkage_paper_cites** Script that searches for articles in common between Google Scholar and accedaCRIS(or any other university) using ***filtered-paper-cites-GS.xlsx*** and ***filtered-paper-cites-CRIS.xlsx*** files. The script generates the file ***record_linkage_paper_cites.xlsx***.

-**gs_foreign_paper_cites:** This script obtains articles from different universities from Google Scholar and separates them into ***train_other_uni_paper_cites.csv*** and ***test_other_uni_paper_cites.csv*** files, which will be used to create the training and test sets of the neural network. You need to indicate the codes that Google Scholar uses to group the different universities for both the articles that will be used to form the training set and the articles that will be used to form the test set.

-**gs_create_train_test_cites:** Script that generates the training and test set from the files ***record_linkage_paper_cites.xlsx***, ***train_other_uni_paper_cites.csv*** and ***test_other_uni_paper_cites.csv***. The names of the created sets are ***train_paper_cites_GS.xlsx*** and ***test_paper_cites_GS.xlsx***.

-**binary_classification_GS:** Script that contains the neural network model.
