# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from gluon import URL, XML, CAT, I

import os
import json

class ContentPhotoset(ContentPlugin):
    """
    Photo set item
    """

    def get_icon(self):
        return I(_class="fa fa-object-group")

    def get_name(self):
        return self.T('Photo Set')


    def create_content(self, item):
        self.db.plugin_photoset_content.insert(
            credit_line="{} {}".format(
                self.auth.user.first_name,
                self.auth.user.last_name
            ),
            item_id=item.unique_id,
            photoset=[]
        )

    def export(self, item, export_dir):
        db = self.db
        ct_table = db.plugin_photoset_content
        ct_photo = db.plugin_photoset_photo
        content = ct_table(item_id=item.unique_id)
        with open(os.path.join(export_dir, 'photoset.json'), 'w') as f:
            f.write(content.as_json())

        for p_id in content.photoset:
            pic = ct_photo(p_id)
            pic_dir = os.path.join(export_dir, str(p_id))
            os.mkdir(pic_dir)
            with open(os.path.join(pic_dir, 'photo.json'), 'w') as f:
                f.write(json.dumps({
                    'id': pic.id,
                    'picture': URL(
                        'default','download', args=[pic.picture],
                        scheme=True, host=True)
                }))

        return


    def get_item_url(self, item):
        return URL('plugin_photoset', 'index.html', args=[item.unique_id])

    def get_changelog_url(self, item):
        return URL('plugin_photoset', 'changelog', args=[item.unique_id])

    def get_full_text(self, item):
        """Return full text document, mean for plugins"""
        photoset_content = self.db.plugin_photoset_content(
            item_id=item.unique_id)
        output = self.response.render(
            'plugin_photoset/full_text.txt',
            dict(photoset_content=photoset_content, item=item))
        return unicode(output.decode('utf-8'))

    def preview(self, item):
        super(ContentPhotoset, self).preview(item)
        photoset_content = self.db.plugin_photoset_content(
            item_id=item.unique_id
        )
        return XML(
            self.response.render(
                'plugin_photoset/preview.html',
                dict(item=item, photoset_content=photoset_content))
        )
