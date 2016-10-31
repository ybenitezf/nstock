# -*- coding: utf-8 -*-
# from https://github.com/web2py/scaffold
if False:
    from gluon import current
    request = current.request
#
# On new installations remove the 'whoosh' directory from the package
# and don't include it on the repository


class Whoosh(object):

    def __init__(self):
        import os
        from whoosh.fields import Schema, TEXT, STORED
        from whoosh.index import create_in, open_dir
        # from whoosh.query import *
        self.index = os.path.join(request.folder, 'whoosh')
        if not os.path.exists(self.index):
            os.mkdir(self.index)
            self.schema = Schema(id=STORED, text=TEXT)
            self.ix = create_in(self.index, self.schema)
        else:
            self.ix = open_dir(self.index)

    def add_to_index(self, item_id, text):
        from whoosh.writing import AsyncWriter
        writer = AsyncWriter(self.ix)
        writer.update_document(id=item_id, text=text.lower())
        writer.commit()

    def search(self, text, page=1, pagelen=5000):
        from whoosh.qparser import QueryParser
        text = text.lower()
        with self.ix.searcher() as searcher:
            query = QueryParser("text", self.ix.schema).parse(text)
            results = searcher.search_page(query, page, pagelen)
            return [r['id'] for r in results]
