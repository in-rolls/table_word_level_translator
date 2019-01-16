## Table Translator: Translate Unique Non-English Words in a Table and Append Their Translations

Use [GoogleTrans](https://github.com/BoseCorp/py-googletrans), a Python client for the free and unlimited---though throttled at about 15 requests/minute---Google Translate Ajax API, to get word-level translations for each unique word and then append translated cell values to the table in columns with column names.

There are four big reasons for using this script: 

1. Given throttling, it is important to reduce the request volume as much as possible. Word level translations are, we think, the best you can do out of the box.

2. The script also builds a word-level translation database to reduce querying volume for multiple files.

3. We get romanized transliterations per word which is often pretty useful. See below on that. And we can append separate columns containing transliteration---based on what the user wants.

4. It is a bit of a pain to get word-level translations for each unique word in a table and then do a column-wise append back to the table. This script does it.

### Why the AJAX API rather than Google Cloud Translation API

Google Cloud Translation API is reasonably priced. That means that for small projects, it doesn't matter whether you use the Ajax API or the official cloud translation API. For large projects, there is a serious trade-off to be considered: between throttling (15 requests per minute) and price. The reason for Ajax API for us is not price but the fact that we can get [romanized transliterations and alternate translations](ajax_api.png) from the Ajax API, which we don't get from the official Translation API. (Translation API just returns 'Pentagon' for the request!) These transliterations are particularly important for proper nouns in Hindi (and plausibly other world languages) for which often there is no established English counterpart.

### Other Related Work

[Table Cell Level Translator](https://github.com/in-rolls/table_cell_level_translator) provides the basic version. 

### Workflow

1. **Get List of Unique Words** The script iterates through all the values in a table and gets a list of all the unique words. (We assume that each word is separated by a space.)

2. **Get Translations (and other returned info.) per Word:** The script run the unique words through Google Translate and produces an intermediate word_info table, which includes all the returned information from Google Translate for a word. (This step is useful because sometimes the translations proposed by Google are off. So we need to rely on other data returned by Google, for e.g., phonetic equivalents of the word in the output language, etc.) We save this table as [word_info.db](word_info.db).

3. **Append Translation Back to the Table:** For each column in the input table, by default, the script then left_joins only the primary translation from the word_info table and appends the translated value into a new column called `source_column_name_output_language`. 

If you want to append information other columns from the word_info table, you need to specify those columns [here](word_info_columns.csv). The output column names become `source_column_name_word_info_column_name_output_language` (Each input column will have as many output columns as we flag in the `word_info_columns.csv` file.

There are two columns in the `word_info_columns.csv` file. `col_name` is `word_info_column_name` and `mapping` is the key to access the data field in the JSON object of the extra data. (e.g. `translation:0:3` means `extra_data['translation'][0][3]`). The `col_name` starts with `#` will be skipped.

The [script](table_translator.py) takes the following options:

```
usage: table_translator.py [-h] [-i INPUT_LANGUAGE] [-l OUTPUT_LANGUAGE]
                           [-r RATE_LIMIT] [-t THREADS] [-p PROXIES]
                           [-w WORD_INFO_FILE] [-c WORD_INFO_COLUMNS]
                           [-o OUTPUT]
                           inputfile

Table Translator: Translate Unique Non-English Words in a Table and
   Append Their Translations

Use GoogleTrans, a Python client for the free and unlimited Google Translate
Ajax API, to get word level translations for each unique word and then append
translated cell values to the table in columns with column names.

Example usage:
    python table_translator.py -o outputfile.csv inputfile.csv

positional arguments:
  inputfile             Input CSV file

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_LANGUAGE, --input-language INPUT_LANGUAGE
                        Input language (Default auto detect)
  -l OUTPUT_LANGUAGE, --output-language OUTPUT_LANGUAGE
                        Output language (Default English)
  -r RATE_LIMIT, --rate-limit RATE_LIMIT
                        Google API requests per MINUTE
  -t THREADS, --threads THREADS
                        Number of threads (Default: 1)
  -p PROXIES, --proxies PROXIES
                        Proxies list file
  -w WORD_INFO_FILE, --word-info-file WORD_INFO_FILE
                        Word info data file
  -c WORD_INFO_COLUMNS, --word-info-columns WORD_INFO_COLUMNS
                        Word info columns which should be included
  -o OUTPUT, --output OUTPUT
                        Output CSV filename
```

### Running The Script

```
pip install -r requirements.txt
python table_translator.py -o output.csv test-input.csv
```

### Authors

Suriyan Laohaprapanon and Gaurav Sood

### License

The package is released under the [MIT License](https://opensource.org/licenses/MIT).
