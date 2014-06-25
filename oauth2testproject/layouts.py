from pyramid_layout.layout import layout_config


@layout_config(
        name='app_layout',
        template='oauth2testproject:templates/layouts/application.pt'
        )
class ApplicationLayout(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
