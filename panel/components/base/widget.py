import param
from panel.widgets.base import Widget
from bokeh.models.layouts import HTMLBox
from bokeh.core import properties


class WebComponentWidget(Widget):
    _tag = ""

    def __init__(self, **params):
        self._widget_type = self._get_bokeh_py_model()

        super().__init__(**params)

    @staticmethod
    def _get_bokeh_property(parameter):
        if isinstance(parameter, param.String):
            return properties.String(default=parameter.default)
        else:
            raise NotImplementedError

    def _get_bokeh_py_model(self):
        class_name = type(self).__name__ + "BKModel"
        bases = (object,)  # bases = (HTMLBox,) raises KeyError

        attributes = {}
        self_keys = set(self.param.objects().keys())
        widget_keys = set(Widget.param.objects().keys())

        for key in (self_keys - widget_keys) - {"_tag"}:
            parameter = self.param.objects()[key]
            bokeh_property = self._get_bokeh_property(parameter)
            attributes[key] = bokeh_property

        return type(class_name, bases, attributes,)

    def _get_bokeh_ts_model(self):
        pass


# See https://www.predix-ui.com/#/elements/px-app-nav
class AppNav(WebComponentWidget):
    _tag = param.String("px-app-nav", constant=True)

    items = param.String(
        '[{"label":"Home","id":"home","icon":"px-fea:home"},{"label":"Alerts","id":"alerts","icon":"px-fea:alerts","metadata":{"openCases":"12","closedCases":"82"}},{"label":"Assets","id":"assets","icon":"px-fea:asset","children":[{"label":"Asset #1","id":"a1"},{"label":"Asset #2","id":"a2"}]},{"label":"Dashboards","id":"dashboards","icon":"px-fea:dashboard","children":[{"label":"See Live Truck View","id":"trucks","icon":"px-obj:truck"},{"label":"Track Orders","id":"orders","icon":"px-fea:orders"},{"label":"Analyze Invoices","id":"invoices","icon":"px-fea:templates"}]}]'
    )


app_nav = AppNav()
app_nav_bokeh_model = app_nav._widget_type()
print(app_nav_bokeh_model)
print(app_nav_bokeh_model.items)
