Input
-List of full text file paths.
-Target language (french default).
-source folder path.

Execution:
For each text file:
1. Create a sub folder with the name of the text file in the source folder.
2. Run the text through the complete workflow. 
3. Create a text file called Engish Sentences.txt in the sub folder and copy the returned English result(corrected and split into sentences).
4. Create a text file called French Sentences.txt in the sub folder and copy the returned French translated results.
5. In the Source folder, create a CSV file if it doesnt exist and add the following:
- filename
-English Sentence Count
-French Sentence Count