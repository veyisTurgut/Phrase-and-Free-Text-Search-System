import os
import string
import threading
import json
import math

FILE_NAMES = [] # this list holds the names of the reuter files.
STOPWORDS = [] # this list holds the stopwords
RETURN_VALUES_OF_THREADS = {} # this dictionary holds the values returned from extractBody function which is executed parallelly by threads.


def getFileNames():
    """
    This function traverses reuters21578 folder and appends names of sgm files to global FILE_NAMES list.
    """
    for file in os.listdir("./reuters21578"):
        if file.endswith(".sgm"):
            FILE_NAMES.append(os.path.join("./reuters21578", file))


def getStopwords():
    """
    This function reads stopwords.txt and stores those stopwords in global STOPWORDS list.
    """
    f = open("./stopwords.txt", "r")
    for line in f.readlines():
        STOPWORDS.append(line.strip())
    f.close()

def invertArticle(ID, TEXT):
    """
    This function returns an inverted index of an article.
    It takes the ID and TEXT part of the article and creates the inverted index.
    Example return value: {"term_1": {ID: [i1, i2, i3, ...]}, "term_2": {ID. [i1, i2, i3, ...]},
                            "term_3": {ID: [i1, i2, i3, ...]}, "term_4": {ID: [i1, i2, i3, ...]},..}
    """
    posting_list = {}
    for idx in range(len(TEXT)):
        current_word = TEXT[idx]
        # for every word in article
        if current_word == '':
            continue
        if current_word not in posting_list:
        # if this word did not already in the posting list, insert it with its location.
            posting_list[current_word] = {ID: [idx]}
        else:
        # if this word were already in the posting list, append new location to location list
            posting_list[current_word][ID].append(idx)
    return posting_list

def merge(postings):
    """
    This function merges the inverted indexes of articles from a file. 
    For every smg sile, this function is called at the end of the "preprocess()" function.

    Example postings content:  {"term_1": {ID: [i1, i2, i3, ...]}, "term_2": {ID. [i1, i2, i3, ...]},
                            "term_3": {ID: [i1, i2, i3, ...]}, "term_4": {ID: [i1, i2, i3, ...]},..}

    Example return value: {"term_1": {ID1: [i1, i2, i3, ...], ID2: [i1, i2, i3, ...], ID999: [i1, i2, i3, ...]]},
                            "term_2": {ID13: [i1, i2, i3, ...], ID2242: [i1, i2, i3, ...], ID10919: [i1, i2, i3, ...]]},
                            "term_3":{ID241: [i1, i2, i3, ...], ID1221: [i1, i2, i3, ...], ID14999: [i1, i2, i3, ...]]},, ...}
    """
    big_posting = {} # this is the return value.
    #print(postings)
    for posting in postings: 
        # posting = "term_1": {ID: [i1, i2, i3, ...]}
        for key, val in posting.items(): 
            # key =  term_1
            # val: {ID: [i1, i2, i3, ...]}
            if key not in big_posting: # if key was not in the list previously, create it
                big_posting[key] = val
            else: # if key is already in the list, append new id next to it.
                for key_,val_ in val.items():
                    big_posting[key][key_] = val_
    return big_posting


def secondIndexBuilder(BODY):
    """
    Example BODY content: ['term1', 'term2', 'term3', 'term1', ...]

    Example return value:{'term1' : TF1, 'term2' : TF2, 'term3' : TF3, ...}
    """
    result = {term:1+ math.log(BODY.count(term),10)  for term in set(BODY) if term != ''}
    return result



def preprocess(file_name):
    """
    This function preprocess the reuters_xx.smg file.
    It reads the file article by article and stores the inverted index of each article in the "postings" variable.
    Then it calls the "merge()" function stores the returned value in global RETURN_VALUES_OF_THREADS variable.
    """
    with open(file_name, "rb") as f:
        contents = f.read().decode("latin-1") # read smg file in latin-1 encoding
        postings = []
        doc_index = {}
        while len(contents) > 0: # read article by article
            article = contents[contents.find("<REUTERS"):contents.find("/REUTERS>")+9] # an article is surrounded with <REUTERS> tags.
            new_id_idx = article.find('NEWID=') # find location of NEWID in the article
            if new_id_idx > -1: # if found assign it to NEWID variable
                NEWID = int(article[new_id_idx+7:article.find('>')-1])
            else: # if not found, move on to next article
                contents = contents[contents.find("/REUTERS>") + 9:]
                continue
            title_idx = article.find("<TITLE>") # title is surrounded with <TITLE> tags. Find its location
            if title_idx > -1: # if found assign it to TITLE variable
                TITLE = article[title_idx+7:article.find("</TITLE>")]
            else: # if not found, assume its empty
                TITLE = ""
            body_idx = article.find("<BODY>") # body is surrounded with <BODY> tags. Find its location
            if body_idx > -1: # if found assign it to BODY variable
                BODY = article[body_idx+6:article.find("</BODY>")]
            else: # if not found, assume its empty
                BODY = ""

            # merge title and body of the article
            BODY = TITLE + " " + BODY

            # case-folding : lower every character in the article
            BODY = BODY.lower()

            # \n removal : remove newline characters from article
            BODY = BODY.replace("\n", " ")

            # stopword removal : remove stopwords from article
            for stopword in STOPWORDS:
                BODY = BODY.replace(' '+stopword+' ', ' ')

            # punctuation removal : remove punctuations by cponverting them to space characters.
            BODY = BODY.translate(BODY.maketrans(
                '', '', string.punctuation)).split(" ")

            # stopword removal (again): remove stopwords from article
            BODY = [elem for elem in BODY if not (elem in STOPWORDS or elem.isnumeric())]

            doc_index[NEWID] = secondIndexBuilder(BODY)

            postings.append(invertArticle(NEWID, BODY)) # append inverted index to the "posting" variable.
            contents = contents[contents.find("/REUTERS>") + 9:] # move on to next article
    
    # store return value of this function in a global variable
    RETURN_VALUES_OF_THREADS[file_name] = [merge(postings),doc_index]


if __name__ == "__main__":
    """
    
    """
    getFileNames() # store filenames in the global variable
    getStopwords() # store stopwords in the global variable

    threads = []
    for file in FILE_NAMES:
        # create threads for preprocessing each file
        extract_body_thread = threading.Thread(target=preprocess, args=(file,))
        threads.append(extract_body_thread)
        extract_body_thread.start()

    for thread in threads:
        # wait for threads to finish
        thread.join()

    biggest_posting = {}
    document_frequencies = {}
    for filename in sorted(RETURN_VALUES_OF_THREADS.keys()):
        # append inverted indexes starting from first file, so that final result can be sorted automatically.
        posting_list = RETURN_VALUES_OF_THREADS[filename][0]
        document_frequencies.update(RETURN_VALUES_OF_THREADS[filename][1])
        for key, val in posting_list.items():
            ## key: term
            ## val: {ID1: [id1, id2, id3, ...]}
            if key not in biggest_posting:
                biggest_posting[key] = val
            else:
                for id,idxs in val.items():
                    ## id: ID1
                    ## idxs = [id1, id2, id3, ...]
                    biggest_posting[key][id] = idxs
    # write index to file in json format
    f1 = open("inverted_index.json", "w")
    json.dump(biggest_posting, f1)
    f2 = open("document_frequency_index.json","w")
    json.dump(document_frequencies, f2)
    