from sqlalchemy import create_engine
from sklearn.feature_extraction.text import CountVectorizer
from nltk.tokenize import sent_tokenize, word_tokenize, MWETokenizer

import regex as re


class QueryStream(object):
    """ 
    Stream documents from the articles database
    Can be subclassed to stream words or sentences from each document
    """
    def __init__(self, sqldb, query=None, idcol='post_id', 
                 textcol='article_text', chunksize=1000):

        self.sql_engine = create_engine(sqldb)
        self.query = query
        self.chunksize = chunksize
        self.textcol = textcol
        self.idcol = idcol

    def __iter__(self):
        """ Iterate through each row in the query """
        query_results = self.sql_engine.execute(self.query)
        result_set = query_results.fetchmany(self.chunksize)
        while result_set:
            for row in result_set:
                yield row
            result_set = query_results.fetchmany(self.chunksize)

class SentenceStream(QueryStream):
    """
    Stream tokenized sentences from a query
    """
    def __init__(self, ngrams=None, *args, **kwargs):
        super(SentenceStream, self).__init__(*args, **kwargs)
        # this will allow us to treat pre-defined n-grams as
        # a single word, e.g., 'hillary_clinton', once
        # we've identified them
        self.mwe = MWETokenizer(ngrams)
        
    def __iter__(self):
        rows = super(SentenceStream, self).__iter__()
        # remove all punctuation, except hyphens
        punct = re.compile("[^A-Za-z0-9\-]")
        
        for doc in rows:
            id = getattr(doc, self.idcol)
            text = getattr(doc, self.textcol)
            
            for sentence in sent_tokenize(text):
                split_sentence = [punct.sub('', word).lower()
                                  for word in word_tokenize(sentence)]
                yield id, self.mwe.tokenize([word for word in split_sentence 
                                             if word.replace('-', '')])