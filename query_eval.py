import json
import datetime
import math


def calculateTermFrequencyOfTheQuery(query: list) -> dict:
    """
    Calculates the term frequency of the input query.
    Example term: wordx
    Example query: [word1, word2, word3, word1, ...]
    Formula: 1 + log_10(document.count(term))

    Example return value: {'term1': TF1, 'term2': TF2, 'term3': TF3}
    """
    return {term: 1 + math.log(query.count(term), 10) for term in query}


def calculateInverseDocumentFrequency(posting_lists: dict) -> dict:
    """
    Calculates the inverse document frequency of the query terms.
    Formula: log_10(N/len(documents that contain term))

    Example posting_lists: {term1: {ID1: [i1, i2, i3, ...], ID2: [i1, i2, i3, ...], ID999: [i1, i2, i3, ...]},
                        term2: {ID1985: [i1, i2, i3, ...], ID2204: [i1, i2, i3, ...], ID9929: [i1, i2, i3, ...]}, ...}

    Example return value: {'term1': IDF1, 'term2': IDF2, 'term3': IDF3, ...}
    """
    return {term: math.log((21578+1)/len(posting_list), 10) if len(posting_list) > 0 else 0 for term, posting_list in posting_lists.items()}


def calculateTfIdfScoreForDocuments(TF_of_documents: dict, IDF_of_document_terms: dict) -> dict:
    """
    Calculates the TF-IDF score of a document.
    Formula: tf[term, document] * idf[term] for each term

    Example TF_of_documents: {"DOC1": {"term1": TF1, "term2": TF2, ...}, "DOC2": {"term1": TF1, "term2": TF2, ...}, ...}
    Example IDF_of_documents: {"term1": IDF1, "term2": IDF2, "term3": IDF3, "term4": IDF4, ...}

    Example return value: {DOC1: {'term1': TF-IDF1, 'term2': TF-IDF2, ...}, DOC6114: {'term1': TF-IDF1, ...}, ...}
    """
    return{doc:{term:TF*IDF_of_document_terms[term]  for term, TF in TF_values.items()} for doc,TF_values in TF_of_documents.items()}


def calculateCosineScore(query: dict, document: dict) -> float:
    """
    Calculates cosine similarity score of the query and a document.
    Formula: sum(query[i]*document[i] for each i) / (sqrt( sum(query[i]^2 for each i) * sum(document[j]^2 for each j))) 
    """
    return sum( query[term]*document[term] if term in document else 0 for term in query) / math.sqrt(sum(query[term]**2 for term in query) * sum(document[term]**2 for term in document))


def freeTextSearch(query_terms, posting_lists: dict, document_terms_postings: dict, DOCUMENT_INDEX: dict) -> list:
    """
    Performs free text search on the index file.
    Steps:
    - find tf values
        - find tf values of query by calling "calculateTermFrequencyOfTheQuery" function above
        - tf values are already in the (DOCUMENT_INDEX parameter)[document_frequency_index.json file] for documents, no need to calculate
    - find idf values
        - find idf values of the query terms
        - find idf valuesof the related document terms
    - find tf-idf for each doc and the query
        - find tf-idf values of the query
        - find tf-idf values of documents
    - calculate cosine similarity of the query and documents
    - sort with respect to cosine similarities in descending order
    """
    related_docs = {doc_id: DOCUMENT_INDEX[doc_id] for doc_id in set([item for sublist in [list(x.keys()) for x in list(posting_lists.values())] for item in sublist])}
    # TF: find tf values of query
    TF_of_query = calculateTermFrequencyOfTheQuery(query_terms)
    # IDF: find idf values of query terms and related document terms
    IDF_of_query = calculateInverseDocumentFrequency(posting_lists)
    IDF_of_document_terms = calculateInverseDocumentFrequency(document_terms_postings)
    # TF-IDF: find tf-idf values of the query and the documents
    TF_IDF_score_of_query = {term: TF_of_query[term] * IDF_of_query[term] for term in TF_of_query.keys()}
    TF_IDF_scores_of_documents = calculateTfIdfScoreForDocuments(related_docs, IDF_of_document_terms)
    print(TF_IDF_scores_of_documents["3190"])
    print(TF_IDF_scores_of_documents["19358"])
    # calculate cosine similarity of the query and documents
    result = {doc_id: calculateCosineScore(TF_IDF_score_of_query, TF_IDF_scores_of_a_document)
              for doc_id, TF_IDF_scores_of_a_document in TF_IDF_scores_of_documents.items()}
    # sort documents with respect to cosine similarities in decreasing order
    #print(IDF_of_query)
    #print(TF_IDF_score_of_query)
    return sorted(result.items(), key=lambda x: x[1], reverse=True)


def intersection(terms, posting_lists):
    """
    Intersects document id's of posting_lists.

    Example terms: ["term1", "term2", ...]
    Example posting_lists: {"term1": {"DOC_ID_546": [TF, [loc1, loc2, loc3, ...]], "DOC_ID_2254": [TF, [loc1, loc2, loc3, ...]], ...}, 
                            "term2": {"DOC_ID_124": [TF, [loc1, loc2, loc3, ...]], "DOC_ID_546": [TF, [loc1, loc2, loc3, ...]], ...}, ... }

    Example return value: [546]
    """
    result = [int(x) for x in posting_lists[terms[0]]]
    # store document ids of first term
    if(len(terms) == 1):
        # if there is onl one term, just return the result
        return result
    for term in terms[1:]:
        # for every document other than the first one, take the intersection
        result = [value for value in result if str(
            value) in posting_lists[term]]
    return result


def chainFind(term_locations):
    """
    Finds consecutive numbers in a list of lists. Might return empty list if no consecutive numbers found.

    Example term_locations: [[26, 34, 46], [27, 42, 47, 56, 89], [28, 31, 44, 48, 75, 456]]

    Example return value: [[26, 27, 28], [46, 47, 48]]
    """

    # when there is only one term, just return the locations
    if len(term_locations) == 1:
        return term_locations[0]

    res = []
    for first_idx in term_locations[0]:
        # for every location in first list
        next_idx = first_idx + 1
        last_idx = first_idx + len(term_locations) - 1
        # store next location and (possible) last position in variables
        for location_list in term_locations[1:]:
            # for other lists
            if not next_idx in location_list:
                # check if next location is present, if not no chain found, start from second location of first file
                break
            elif next_idx == last_idx:
                # if chain did not broke until the last position, then we found the exact phrase, store it.
                res.append([x for x in range(first_idx, last_idx + 1)])
            # move on to next document and check next location.
            next_idx += 1
    # return all chains
    return res


def phraseSearch(terms, posting_lists: dict) -> dict:
    """
    Performs phrase search on the index file.
    Steps:
    - find possible documents that phrase might occur by intersecting document id's of each term
    - find location of terms in those possible documents
    - find consecutive numbers in those locations so that we can identify beginning and end of phrases' indexes
    - return found locations and document id's
    """
    # result = {} # from previous version where I print out locations as well as the document ids
    result = []
    possible_documents = intersection(terms, posting_lists)
    # intersect document id's of terms. since this is a phrase search, we must only look at the files that contain all of the terms
    term_locations_on_these_documents = {doc: [posting_lists[term][str(doc)] for term in terms] for doc in possible_documents}
    # extract term document_ids and term locations from index file.
    for doc in term_locations_on_these_documents:
        # for every possible document that might contain phrase
        res = chainFind(term_locations_on_these_documents[doc])
        # find chains
        if res == []:
            # do not add documents that fail to contain a phrase
            continue
        # result[doc] = res  # from previous version where I print out locations as well as the document ids
        result.append(doc)
    return result


def readIndexFileForQuery(query_terms: list, INVERTED_INDEX: dict, DOCUMENT_INDEX: dict) -> dict:
    """
    Reads the input query and INDEX file, then returns posting lists of query_terms.
    """
    query_postings = {term: INVERTED_INDEX.get(term) if INVERTED_INDEX.get(
        term) != None else {} for term in query_terms}
    related_docs = {doc_id: DOCUMENT_INDEX[doc_id] for doc_id in set(
        [item for sublist in [list(x.keys()) for x in list(query_postings.values())] for item in sublist])}
    document_terms_postings = {term: INVERTED_INDEX.get(
        term) if INVERTED_INDEX.get(term) != None else {} for term in set([item for sublist in [x.keys() for x in related_docs.values()] for item in sublist])}
    return query_postings, document_terms_postings


def search(query_terms: list, query_type: str, INVERTED_INDEX: dict, DOCUMENT_INDEX: dict):
    """
    Decides the type of the query and calls corresponding functions.
    """
    # posting list merging for different types of queries
    if query_type == "phrase":
        query_postings, document_terms_postings = readIndexFileForQuery(
            query_terms, INVERTED_INDEX, DOCUMENT_INDEX)
        result = phraseSearch(query_terms, query_postings)
    if query_type == "free-text":
        query_postings, document_terms_postings = readIndexFileForQuery(
            list(set(query_terms)), INVERTED_INDEX, DOCUMENT_INDEX)
        result = freeTextSearch(
            query_terms, query_postings, document_terms_postings, DOCUMENT_INDEX)
    return result


if __name__ == "__main__":

    # first load index_files to memory
    inverted_index_file = open('./inverted_index.json',)
    INVERTED_INDEX = json.load(inverted_index_file)
    inverted_index_file.close()
    document_index_file = open('./document_frequency_index.json',)
    DOCUMENT_INDEX = json.load(document_index_file)
    document_index_file.close()

    # add timestamp to the name of the output file
    file_name = "result_" + str(datetime.datetime.now()) + ".json"
    overall_result = {}

    while True:
        # wait input from user continously
        terms = []
        query = input(
            "\x1b[1;37;44m What is your search query? \x1b[1;37;41m(Press q for quit.)\x1b[0m ").lower()
        if query == "q":
            # if user typed 'q', close the program.
            f = open(file_name, "w")
            json.dump(overall_result, f, indent=4)
            f.close()
            print("Now you can see all the contents in", file_name, "file.")
            break
        else:
            # split the input to words and decide type of it.
            trimmed_query = query.strip()

            if len(trimmed_query) == 0 or (trimmed_query[0] == '"' and not trimmed_query[-1] == '"') or (not trimmed_query[0] == '"' and trimmed_query[-1] == '"'):
                print("Wrong input, please try again!")
                continue
            elif trimmed_query[0] == '"' and trimmed_query[-1] == '"':
                if trimmed_query[1:-1] == "":
                    print("Wrong input, please try again!")
                    continue
                # phrase query
                result = search(
                    trimmed_query[1:-1].split(), "phrase", INVERTED_INDEX, DOCUMENT_INDEX)
                overall_result[query[1:-1]] = result
            else:
                # free text query
                result = search(trimmed_query.split(), "free-text",
                                INVERTED_INDEX, DOCUMENT_INDEX)
                overall_result[query] = result
            # print(result)
            print("Result is saved to", file_name,
                  "file. You can see it after closing the program.")
