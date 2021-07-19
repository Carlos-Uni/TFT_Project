import re
import itertools
import argparse
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.utils import class_weight
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import layers

plt.style.use('ggplot')
#collects the accuracy and loss of the training process and create a plot of this data.
def plot_history(history):
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    x = range(1, len(acc) + 1)

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(x, acc, 'b', label='Training acc')
    plt.plot(x, val_acc, 'r', label='Validation acc')
    plt.title('Training and validation accuracy')
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.plot(x, loss, 'b', label='Training loss')
    plt.plot(x, val_loss, 'r', label='Validation loss')
    plt.title('Training and validation loss')
    plt.legend()
    plt.savefig('train_data.png', bbox_inches='tight')
    plt.close()

#creates the confusion matrix using the predicted data from the test dataframe
def plot_confusion_matrix(cm, classes,
                        normalize=False,
                        title='Confusion matrix',
                        cmap=plt.cm.Blues):

	plt.imshow(cm, interpolation='nearest', cmap=cmap)
	plt.title(title)
	plt.colorbar()
	tick_marks = np.arange(len(classes))
	plt.xticks(tick_marks, classes, rotation=45)
	plt.yticks(tick_marks, classes)

	if normalize:
	    cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
	    print("Normalized confusion matrix")
	else:
	    print('Confusion matrix, without normalization')

	print(cm)

	thresh = cm.max() / 2.
	for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
	    plt.text(j, i, cm[i, j],
	        horizontalalignment="center",
	        color="white" if cm[i, j] > thresh else "black")

	plt.tight_layout()
	plt.ylabel('True label')
	plt.xlabel('Predicted label')
	plt.savefig('test_CM.png', bbox_inches='tight')
	plt.close()

if __name__ == '__main__':

	#check that the parameters are correct.
	def file_checker(selection, files_name):
		if selection not in files_name:
			parser.error("The file " + files_name + " is incorrect. Use the -h command to see the format and run the script correctly.")
		return files_name

	parser = argparse.ArgumentParser(description="Script that contains the neural network model")
	parser.add_argument("train_set", metavar='train_paper_cites_GS.xlsx', 
			type=lambda s:file_checker('train_paper_cites_GS.xlsx', s),
	        help="File that contains the training set")
	parser.add_argument("test_set", metavar='test_paper_cites_GS.xlsx', 
			type=lambda s:file_checker('test_paper_cites_GS.xlsx',s),
	        help="File that contains the test set")
	args = parser.parse_args()

	train_data = pd.read_excel(args.train_set, engine="openpyxl")
	test_data = pd.read_excel(args.test_set, engine="openpyxl")

	#fill NaN values in train and test data
	most_repeated_year = train_data['Year'].mode().values
	train_data['Journal'] = train_data['Journal'].fillna("a")
	train_data['Year'] = train_data['Year'].fillna(most_repeated_year[0]).astype(int).astype(str)
	train_data['Authors'] = train_data['Authors'].fillna("a")

	most_repeated_year = test_data['Year'].mode().values
	test_data['Journal'] = test_data['Journal'].fillna("a")
	test_data['Year'] = test_data['Year'].fillna(most_repeated_year[0]).astype(int).astype(str)
	test_data['Authors'] = test_data['Authors'].fillna("a")

	#the columns and their maximum size that are used in Word Embeddings process
	columns_to_extract = ['GS-Code', 'Article', 'Authors', 'Journal', 'Year']
	maxlength = [1,25,15,15,1]
	maxlength_sum = sum(maxlength)

	#tokenizer is initialized without filters and the special word <pad> is added to the vocabulary
	tokenizer = Tokenizer(filters='')
	tokenizer.fit_on_texts(['<pad>'])

	#creates the vocabulary from the training dataframe and apply a regular expression to all columns except GS-Code
	for column_name in columns_to_extract:
		if column_name != 'GS-Code':
			train_data[column_name] = train_data[column_name].apply(lambda x : " ".join(re.findall(r"[\w']{3,}|[a-zA-Z][0-9]|[0-9]+",str(x))))
		tokenizer.fit_on_texts(train_data[column_name].values)

	#tokenize the content of the dataframes into a list of integers using the vocabulary
	train_data[columns_to_extract] = train_data[columns_to_extract].apply(lambda x: tokenizer.texts_to_sequences(x))
	test_data[columns_to_extract] = test_data[columns_to_extract].apply(lambda x: tokenizer.texts_to_sequences(x))

	#each column has a maximum word size and is filled with the special word <pad> in case it doesn’t reach that size.
	train_data['GS-Code'] = train_data['GS-Code'].apply(lambda x: x + [tokenizer.word_index['<pad>']]*(maxlength[0] - len(x)))
	train_data['Article'] = train_data['Article'].apply(lambda x: x[:maxlength[1]] + [tokenizer.word_index['<pad>']]*(maxlength[1] - len(x)))
	train_data['Authors'] = train_data['Authors'].apply(lambda x: x[:maxlength[2]] + [tokenizer.word_index['<pad>']]*(maxlength[2] - len(x)))
	train_data['Journal'] = train_data['Journal'].apply(lambda x: x[:maxlength[3]] + [tokenizer.word_index['<pad>']]*(maxlength[3] - len(x)))
	train_data['Year'] = train_data['Year'].apply(lambda x: x + [tokenizer.word_index['<pad>']]*(maxlength[4] - len(x)))

	test_data['GS-Code'] = test_data['GS-Code'].apply(lambda x: x + [tokenizer.word_index['<pad>']]*(maxlength[0] - len(x)))
	test_data['Article'] = test_data['Article'].apply(lambda x: x[:maxlength[1]] + [tokenizer.word_index['<pad>']]*(maxlength[1] - len(x)))
	test_data['Authors'] = test_data['Authors'].apply(lambda x: x[:maxlength[2]] + [tokenizer.word_index['<pad>']]*(maxlength[2] - len(x)))
	test_data['Journal'] = test_data['Journal'].apply(lambda x: x[:maxlength[3]] + [tokenizer.word_index['<pad>']]*(maxlength[3] - len(x)))
	test_data['Year'] = test_data['Year'].apply(lambda x: x + [tokenizer.word_index['<pad>']]*(maxlength[4] - len(x)))

	#all integer lists of all columns are merged into a single one
	train_data['Tokenized_text'] = train_data[columns_to_extract].apply(lambda x: x.sum(), axis=1)
	test_data['Tokenized_text'] = test_data[columns_to_extract].apply(lambda x: x.sum(), axis=1)


	#prepare train and test data
	X_train = np.array(train_data['Tokenized_text'].values.tolist())
	y_train = train_data['Label'].to_numpy()

	X_test = np.array(test_data['Tokenized_text'].values.tolist())
	y_test = test_data['Label'].to_numpy()

	#adding 1 because of reserved 0 index
	vocab_size = len(tokenizer.word_index) + 1
	#a vocabulary is created from the function that examines the distribution of labels and produces weights to 
	#balance equally the under or over-represented classes in the training set.
	class_weights = class_weight.compute_class_weight('balanced', np.unique(y_train), y_train)
	class_weight_dict = dict(enumerate(class_weights))

	model = Sequential([
		tf.keras.layers.Embedding(input_dim=vocab_size, 
	                           output_dim=25, 
	                           input_length=maxlength_sum),
		tf.keras.layers.GlobalMaxPool1D(),
		tf.keras.layers.Dense(64, activation='relu'),
		tf.keras.layers.Dropout(0.2),
		tf.keras.layers.Dense(32, activation='relu'),
		tf.keras.layers.Dropout(0.2),
		tf.keras.layers.Dense(1, activation='sigmoid')])


	model.compile(optimizer=Adam(learning_rate=0.01), loss=tf.keras.losses.binary_crossentropy, metrics=['accuracy'])

	train_history = model.fit(X_train, y_train, validation_split=0.2, epochs=20, shuffle=True, class_weight=class_weight_dict, verbose=2)
	
	train_loss, train_accuracy = model.evaluate(X_train, y_train, verbose=False)
	test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=False)

	print("Training Accuracy:  {:.4f}".format(train_accuracy))
	print("Testing Accuracy:  {:.4f}".format(test_accuracy))
	plot_history(train_history)


	test_predictions = model.predict(X_test)
	test_rounded_predictions = test_predictions.round().astype(int)
	cm_test = confusion_matrix(y_true=y_test, y_pred=test_rounded_predictions)
	cm_plot_labels = ['no_belong','belong']
	plot_confusion_matrix(cm=cm_test, classes=cm_plot_labels, title='Test Confusion Matrix')
	
