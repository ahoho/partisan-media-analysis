#stream.py
from sqlalchemy import create_engine
from sklearn.feature_extraction.text import CountVectorizer
import cPickle as pickle
from scipy import io


class QueryStream(object):
    """ 
    Stream documents from the articles database
    Can be subclassed to stream words or sentences from each document
    """
    def __init__(self, sqldb, query=None, textcol='article_text', chunksize=1000, **kwargs):

        self.sql_engine = create_engine(sqldb)
        self.query = query
        self.chunksize = chunksize
        self.analyze = CountVectorizer(**kwargs).build_analyzer()
        self.textcol = textcol

    def __iter__(self):
        """ Iterate through each row in the query """
        query_results = self.sql_engine.execute(self.query)
        result_set = query_results.fetchmany(self.chunksize)
        while result_set:
            for row in result_set:
                yield getattr(row, self.textcol)
            result_set = query_results.fetchmany(self.chunksize)


sql_url = 'postgres://postgres:postgres@localhost/articles'
query = """
        SELECT post_id, article_text FROM articles
        WHERE num_words > 200
        ORDER BY post_id
        LIMIT 5
        """

query = """
        SELECT post_id, article_text
        FROM (SELECT post_id, article_text,
                    ROW_NUMBER() OVER (partition BY url ORDER BY date) AS rnum
              FROM articles
              WHERE num_words > 200) t
        WHERE t.rnum = 1 
        """
id_stream = QueryStream(sql_url, query, textcol='post_id')
post_ids = [id for id in id_stream]

for i in range(1, 6):

    print 'on model {}'.format(i)
    text_stream = QueryStream(sql_url, query)
    vectorizer = CountVectorizer(ngram_range=(i, i), min_df=10)
    tdm = vectorizer.fit_transform(text_stream)

    vectorizer.stop_words_ = None

    with open('./intermediate/vectorizer_{}.pkl'.format(i), 'wb') as vecf,\
         open('./intermediate/post_ids_{}.pkl'.format(i), 'wb') as idf,\
         open('./intermediate/tdm_{}.pkl'.format(i), 'wb') as tdmf:

        # vectorizer 
        pickle.dump(vectorizer, vecf)
        print 'vectorizer {} saved'.format(i)

        # post_ids
        pickle.dump(post_ids, idf)

        # tdm        
        pickle.dump(tdm, tdmf, pickle.HIGHEST_PROTOCOL)
        print 'tdm {} saved'.format(i)

## TO DO!!! 
# Improve tokenization stream

#http://stackoverflow.com/questions/8955448/save-load-scipy-sparse-csr-matrix-in-portable-data-format
#http://stackoverflow.com/questions/10592605/save-classifier-to-disk-in-scikit-learn

