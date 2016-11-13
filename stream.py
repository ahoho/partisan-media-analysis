import re

from sqlalchemy import create_engine
from sklearn.feature_extraction.text import CountVectorizer
from nltk.tokenize import sent_tokenize, word_tokenize

class QueryStream(object):
    """ 
    Stream documents from the articles database
    Can be subclassed to stream words or sentences from each document
    """
    def __init__(self, sqldb, query=None, textcol='article_text', chunksize=1000, **kwargs):

        self.sql_engine = create_engine(sqldb)
        self.query = query
        self.chunksize = chunksize
        self.textcol = textcol

    def __iter__(self):
        """ Iterate through each row in the query """
        query_results = self.sql_engine.execute(self.query)
        result_set = query_results.fetchmany(self.chunksize)
        while result_set:
            for row in result_set:
                yield getattr(row, self.textcol)
            result_set = query_results.fetchmany(self.chunksize)
        return [row.base_url for row in results]

class SentenceStream(QueryStream):
    def __iter__(self):
        rows = super(SentenceStream, self).__iter__()

        for doc in rows:
            for sentence in sent_tokenize(doc):
                yield [word for word in word_tokenize(sentence) if ]

class DocStream(QueryStream):
    def __iter__(self):
        rows = super(DocStream, self).__iter__()

        for row in rows:
            yield self.analyze(row)

class WordStream(DocStream):
    def __iter__(self):
        docs = super(WordStream, self).__iter__()

        for doc in docs:
            for word in doc:
                yield word