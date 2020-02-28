"""Implementation of the Predix App Navigation Widget

See https://www.predix-ui.com/#/elements/px-app-nav"""
import param

from panel.tests.components.data.components.predix.models import PxAppNav as _BkPxAppNav
from panel.widgets.base import Widget


class PxAppNav(Widget):
    """A Predix App Navigation Widget

    See https://www.predix-ui.com/#/elements/px-app-nav"""

    _rename = {"title": None}
    _widget_type = _BkPxAppNav

    items = param.String('{"label":"Home","id":"home","icon":"px-fea:home"}')


if __name__.startswith("bk"):
    import panel as pn

    pn.config.js_files[
        "predix"
    ] = "https://www.predix-ui.com/bower_components/webcomponentsjs/webcomponents-hi.js"

    nav = PxAppNav()

    pn.Column(nav, pn.Param(nav.param.items)).servable()
