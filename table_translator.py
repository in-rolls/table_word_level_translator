#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Table Translator: Translate Unique Non-English Words in a Table and
   Append Their Translations

Use GoogleTrans, a Python client for the free and unlimited Google Translate
Ajax API, to get word level translations for each unique word and then append
translated cell values to the table in columns with column names.

Example usage:
    python table_translator.py -o outputfile.csv inputfile.csv
"""

import os
import sys
import argparse
import string
import time
import sqlite3
import json
import re

import pandas as pd
from googletrans import Translator


def isEnglish(s):
    if len(s) > 0:
        return s[0] in string.printable
    else:
        return False


def get_non_eng_unique_values(df):
    cell_values = set()
    for c in df.columns:
        for term in df[c].unique():
            if type(term) is str:
                term = term.strip()
                if not isEnglish(term):
                    cell_values.add(term)
    print("Number of Non-English unique cell values: {:d}, length: {:d}"
          .format(len(cell_values), len(''.join(cell_values))))
    txt = ' '.join(cell_values)
    words = set(txt.split())
    non_eng_words = []
    for w in words:
        if not isEnglish(w):
            non_eng_words.append(w)
    print("Number of Non-English unquie words: {:d}, length: {:d}"
          .format(len(non_eng_words), len(''.join(non_eng_words))))

    return cell_values, non_eng_words


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def bulk_words_translation(args, words):
    try:
        conn = sqlite3.connect(args.word_info_file, isolation_level=None)
        conn.text_factory = str
        conn.row_factory = dict_factory
        c = conn.cursor()
        # Create table
        c.execute('''CREATE TABLE IF NOT EXISTS words
                    (word text, input_lang text, output_lang text, translate text,
                    extra_data text)''')

        trans_dict = {}

        translator = Translator()
        count = 1
        for w in words:
            print("Translating ({:d}/{:d})...".format(count, len(words)))
            c.execute('SELECT translate, extra_data FROM words WHERE word=?'
                      ' and output_lang=?', (w, args.output_language))
            data = c.fetchone()
            if data is None:
                retry = 0
                while True:
                    try:
                        print("- Google Translate AJAX API request...")
                        if args.input_language is None:
                            trans = translator.translate(w, dest=args.output_language)
                            extra_data = trans.extra_data
                            text = trans.text
                            input_language = extra_data.get('original-language', None)
                        else:
                            trans = translator.translate(w, src=args.input_language,
                                                        dest=args.output_language)
                            extra_data = trans.extra_data
                            text = trans.text
                            input_language = args.input_language
                        time.sleep(60.0 / args.rate_limit)
                        # Insert a row of data
                        c.execute("INSERT INTO words VALUES (?, ?, ?, ?, ?)",
                                (w, input_language, args.output_language,
                                    text, json.dumps(extra_data)))
                        # Save (commit) the changes
                        #conn.commit()
                        data = {'translate': text,
                                'extra_data': extra_data}
                        break
                    except Exception as e:
                        print('ERROR: {!s}'.format(e))
                        retry += 1
                        if retry > 5:
                            print("ERROR: Too many retries, please try again later.")
                            sys.exit(-1)
                        print("Wait 30s and retry...({:d})".format(retry))
                        time.sleep(30)
                        
            else:
                print("- Found in word info database...")
                #print(w, data['translate'])
            trans_dict[w] = data
            count += 1
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
    except Exception as e:
        print('ERROR: {!s}'.format(e))
    finally:
        conn.close()
    return trans_dict


def get_translate(trans_dict, text):
    try:
        trans = []
        for t in trans_dict[text]:
            trans.append(t['translate'])
        text = ''.join(trans)
        return text
    except Exception as e:
        return text


def get_extra_data(trans_dict, text, mapping):
    val = None
    if text in trans_dict:
        m_arr = mapping.split(':')
        v_arr = []
        for w in trans_dict[text]:
            if 'extra_data' in w:
                json_extra_data = None
                try:
                    json_extra_data = json.loads(w['extra_data'])
                    v = json_extra_data[m_arr[0]]
                    for idx in m_arr[1:]:
                        v = v[int(idx)] 
                    if type(v) is unicode:
                        v = v.encode('utf-8')
                    v_arr.append('{!s}'.format(v))
                except Exception as e:
                    print('ERROR: {!s}'.format(e))
                    if json_extra_data:
                        print('DATA: {!s}'.format(json_extra_data))
                    print('MAPPING: {!s}'.format(mapping))
        val = ' '.join(v_arr)
    return val


def build_cell_trans_dict(cell_values, words_dict):
    cell_trans_dict = {}
    for c in cell_values:
        cs = re.split(r'(\s+)', c)
        dest = []
        for w in cs:
            dest.append(words_dict[w] if w in words_dict else {'translate': w})
        cell_trans_dict[c] = dest

    return cell_trans_dict


def main(args):
    df = pd.read_csv(args.inputfile)
    unique_cells, unique_words = get_non_eng_unique_values(df)
    words_dict = bulk_words_translation(args, unique_words)
    trans_dict = build_cell_trans_dict(unique_cells, words_dict)
    winfo_cols = pd.read_csv(args.word_info_columns)
    for col in df.columns:
        col_name = '{:s}_{:s}'.format(col, args.output_language)
        df[col_name] = df[col].apply(lambda c: get_translate(trans_dict, c))
        for wc in winfo_cols.iterrows():
            if wc[1].col_name.startswith('#'):
                continue
            mapping = wc[1].mapping
            col_name = '{:s}_{:s}_{:s}'.format(col, wc[1].col_name,
                                               args.output_language)
            df[col_name] = df[col].apply(lambda c: get_extra_data(trans_dict,
                                                                  c, mapping))
    df.to_csv(args.output, index=False, encoding='utf-8')
    print("Complete!!!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('inputfile', default=None,
                        help='Input CSV file')
    parser.add_argument('-i', '--input-language', default=None,
                        help='Input language (Default auto detect)')
    parser.add_argument('-l', '--output-language', default='en',
                        help='Output language (Default English)')
    parser.add_argument('-r', '--rate-limit', type=int, default=15,
                        help='Google API requests per MINUTE')
    parser.add_argument('-w', '--word-info-file', default='word_info.db',
                        help='Word info data file')
    parser.add_argument('-c', '--word-info-columns',
                        default='word_info_columns.csv',
                        help='Word info columns which should be included')
    parser.add_argument('-o', '--output', default='output.csv',
                        help='Output CSV filename')

    args = parser.parse_args()

    print(args)

    main(args)
