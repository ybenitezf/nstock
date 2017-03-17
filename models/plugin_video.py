# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from plugin_ckeditor import CKEditor
from gluon.tools import PluginManager

class ContentVideo(ContentPlugin):

    def get_item_url(self, item):
        return URL('plugin_video', 'index.html', args=[item.unique_id])


    def create_content(self, item):
        self.db.plugin_video_content.insert(
            credit_line="{} {}".format(
                self.auth.user.first_name,
                self.auth.user.last_name
            ),
            description='',
            item_id=item.unique_id,
            renditions=[]
        )


    def get_icon(self):
        return I(_class="fa fa-file-video-o")

    def get_name(self):
        return self.T("Video")


    def preview(self, item):
        """
        Show the item preview on list's or in packages.
        """
        super(ContentVideo, self).preview(item)
        info = self.db.plugin_video_content(item_id=item.unique_id)
        return XML(
            self.response.render(
                'plugin_video/preview.html',
                dict(item=item, info=info)))


    def export(self, item, export_dir):
        """
        export the video item
        """
        import os
        import json

        # put the video general info
        db  = self.db
        content = db.plugin_video_content(item_id=item.unique_id)
        with open(os.path.join(export_dir, 'video.json'), 'w') as f:
            f.write(content.as_json())

        for r_id in content.renditions:
            # for eatch rendition put the descriptive info and the video link
            rend = db.plugin_video_rendition(r_id)
            rend_dir = os.path.join(export_dir, str(r_id))
            os.mkdir(rend_dir)
            with open(os.path.join(rend_dir, 'rendition.json'), 'w') as f:
                f.write(json.dumps({
                    'id': rend.id,
                    'purpose': rend.purpose,
                    'video': URL(
                        'default', 'download', args=[rend.video],
                        scheme=True, host=True),
                }))

        # done
        return


    def get_changelog_url(self, item):
        return URL('plugin_video', 'changelog', args=[item.unique_id])

    def get_full_text(self, item):
        """Return full text document, mean for plugins"""
        from html2text import html2text

        info = self.db.plugin_video_content(item_id=item.unique_id)
        output = "{}\n{}".format(
            info.credit_line,
            html2text(info.description.decode('utf-8')),
        )
        return unicode(output.decode('utf-8'))


# define tables of this plugin
def _():
    plugins = PluginManager('video', app=None)
    if plugins.video.app is not None:
        # this will register the content/type on the application
        plugins.video.app.registerContentType('video', ContentVideo())
        if not hasattr(db, 'plugin_video_content'):
            # the video files
            tbl = db.define_table(
                'plugin_video_rendition',
                Field('purpose', 'string', length=50, default='web'),
                Field(
                    'video', 'upload', uploadseparate=True, autodelete=True
                ),
            )
            tbl.purpose.comment = T('''
            Descrive the purpose of this rendition of the video, e.g.:
            web, social networks, etc.
            ''')
            tbl.purpose.label = T('Purpose')
            tbl.video.label = T('Video')
            tbl.video.requires = IS_NOT_EMPTY()
            # configure ckeditor
            editor = CKEditor(db=db)
            # content description
            tbl = db.define_table(
                'plugin_video_content',
                Field('credit_line', 'string', length=150, default=''),
                Field(
                    'description', 'text',
                    label=T('Description'),
                    default=''
                ),
                Field('renditions', 'list:reference plugin_video_rendition'),
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

            # enable record  versioning
            tbl._enable_record_versioning()
            # add callback for item cleanup on delete.
            def __plugin_video_item_on_delete(s):
                item = s.select().first()
                if item.item_type == 'video':
                    # cleanup here
                    cnt = db.plugin_video_content(item_id=item.unique_id)
                    db(
                        db.plugin_video_rendition.id.belongs(
                            cnt.renditions)).delete()
                    db(
                        db.plugin_video_content.item_id == item.unique_id
                    ).delete()

                return False  # remember to procced
            db.item._before_delete.insert(0, __plugin_video_item_on_delete)
    return
_()
