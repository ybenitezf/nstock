# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from gluon import URL, XML, CAT, I

import os
import shutil


class ContentPicture(ContentPlugin):


    def get_icon(self):
        return I(_class='fa fa-picture-o')


    def get_name(self):
        return self.T('Picture')


    def create_content(self, item):
        self.db.plugin_picture_info.insert(
            item_id=item.unique_id,
            renditions=[]
        )


    def export(self, item, export_dir):
        """
        Export picture content to export_dir
        """
        # put the picture general info
        db  = self.db
        pic_info = db.plugin_picture_info(item_id=item.unique_id)
        with open(os.path.join(export_dir, 'picture.json'), 'w') as f:
            f.write(pic_info.as_json())

        for r_id in pic_info.renditions:
            # for eatch rendition put the descriptive info and the image
            rend = db.plugin_picture_rendition(r_id)
            exp_info = db(db.plugin_picture_rendition.id == r_id).select(
                db.plugin_picture_rendition.id,
                db.plugin_picture_rendition.purpose,
                db.plugin_picture_rendition.height,
                db.plugin_picture_rendition.width,
                db.plugin_picture_rendition.color,
                db.plugin_picture_rendition.format
            ).first()
            rend_dir = os.path.join(export_dir, str(r_id))
            os.mkdir(rend_dir)
            with open(os.path.join(rend_dir, 'rendition.json'), 'w') as f:
                f.write(exp_info.as_json())
            (filename, stream) = db.plugin_picture_rendition.picture.retrieve(
                rend.picture)
            # normalize filename
            filename = filename.lower()
            shutil.copyfileobj(
                stream,
                open(os.path.join(rend_dir, filename), 'wb')
            )

        # done
        return


    def get_item_url(self, item):
        return URL('plugin_picture', 'index.html', args=[item.unique_id])

    def get_full_text(self, item):
        """Return full text document, mean for plugins"""
        pic_info = self.db.plugin_picture_info(item_id=item.unique_id)
        output = self.response.render(
            'plugin_picture/full_text.txt',
            dict(pic_info=pic_info, item=item))
        return unicode(output.decode('utf-8'))

    def get_changelog_url(self, item):
        return URL('plugin_picture', 'changelog', args=[item.unique_id])

    def preview(self, item):
        super(ContentPicture, self).preview(item)
        info = self.db.plugin_picture_info(item_id=item.unique_id)
        return XML(
            self.response.render(
                'plugin_picture/preview.html',
                dict(item=item, info=info)))
