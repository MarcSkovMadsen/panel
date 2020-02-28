"""Implementation of the Predix App Navigation Widget

See https://www.predix-ui.com/#/elements/px-app-nav"""
import pathlib

from bokeh.core import properties
from bokeh.models.layouts import HTMLBox

PXAPPNAV_TS_PATH = pathlib.Path(__file__).parent / "px_app_nav.ts"
PXAPPNAV_TS_STR = str(PXAPPNAV_TS_PATH.resolve())


class PxAppNav(HTMLBox):
    """A Predix App Navigation Widget

    See https://www.predix-ui.com/#/elements/px-app-nav"""

    __implementation__ = PXAPPNAV_TS_STR

    items = properties.String('{"label":"Home","id":"home","icon":"px-fea:home"}')
