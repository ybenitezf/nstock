# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from gluon.tools import PluginManager
from plugin_ckeditor import CKEditor


class ContentAudio(ContentPlugin):

    def create_content(self, item):
        self.db.plugin_audio_content.insert(
            credit_line="{} {}".format(
                self.auth.user.first_name,
                self.auth.user.last_name
            ),
            description='',
            renditions=[],
            item_id=item.unique_id
        )


    def get_icon(self):
        return I(_class="fa fa-file-audio-o")


    def get_name(self):
        return self.T("Audio")


    def get_item_url(self, item):
        return URL('plugin_audio', 'index.html', args=[item.unique_id])


    def preview(self, item):
        """
        Show the item preview on list's or in packages.
        """
        super(ContentAudio, self).preview(item)
        content = self.db.plugin_audio_content(item_id=item.unique_id)
        return XML(
            self.response.render(
                'plugin_audio/preview.html',
                dict(item=item, info=content)))


    def get_full_text(self, item):
        """Return full text document, mean for plugins"""
        return unicode('')


    def export(self, item, export_dir):
        """
        export the audio item
        """
        import os
        import json

        # put the audio general info
        db  = self.db
        content = db.plugin_audio_content(item_id=item.unique_id)
        with open(os.path.join(export_dir, 'audio.json'), 'w') as f:
            f.write(content.as_json())

        for r_id in content.renditions:
            # for eatch rendition put the descriptive info and the audio link
            rend = db.plugin_audio_rendition(r_id)
            rend_dir = os.path.join(export_dir, str(r_id))
            os.mkdir(rend_dir)
            with open(os.path.join(rend_dir, 'rendition.json'), 'w') as f:
                f.write(json.dumps({
                    'id': rend.id,
                    'purpose': rend.purpose,
                    'audio': URL(
                        'default', 'download', args=[rend.audio],
                        scheme=True, host=True),
                }))

        # done
        return


def _():
    plugins = PluginManager('audio', app=None)
    if plugins.audio.app is not None:
        plugins.audio.app.registerContentType('audio', ContentAudio())
        # the audio rendentions
        tbl = db.define_table(
        # register my content type plugin
            'plugin_audio_rendition',
            Field('purpose', 'string', length=50, default='web'),
            Field(
                'audio', 'upload', uploadseparate=True, autodelete=True
            ),
        )
        tbl.purpose.comment = T('''
        Descrive the purpose of this rendition of the video, e.g.:
        web, social networks, etc.
        ''')
        tbl.purpose.label = T('Purpose')
        tbl.audio.label = T('Audio File')
        tbl.audio.requires = IS_NOT_EMPTY()
        # configure ckeditor
        editor = CKEditor(db=db)
        # content table
        tbl = db.define_table(
            'plugin_audio_content',
            Field('credit_line', 'string', length=150, default=''),
            Field(
                'description', 'text',
                label=T('Description'),
                default=''
            ),
            Field('renditions', 'list:reference plugin_audio_rendition'),
            Field('item_id', 'string', length=64),
            auth.signature,
        )
        tbl.item_id.readable = False
        tbl.item_id.writable = False
        tbl.credit_line.label = T("Credit line")
        tbl.description.label = T('Description')
        tbl.description.widget = editor.widget
        tbl.renditions.label = T("Renditions")
        tbl.renditions.default = []
        tbl.renditions.writable = False
        tbl.renditions.readable = False
        tbl._enable_record_versioning()
_()
