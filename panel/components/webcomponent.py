import panel as pn
import param

TAG = "px-app-nav"
ITEMS = '[{"label":"Home","id":"home","icon":"px-fea:home"},{"label":"Alerts","id":"alerts","icon":"px-fea:alerts","metadata":{"openCases":"12","closedCases":"82"}},{"label":"Assets","id":"assets","icon":"px-fea:asset","children":[{"label":"Asset #1","id":"a1"},{"label":"Asset #2","id":"a2"}]},{"label":"Dashboards","id":"dashboards","icon":"px-fea:dashboard","children":[{"label":"See Live Truck View","id":"trucks","icon":"px-obj:truck"},{"label":"Track Orders","id":"orders","icon":"px-fea:orders"},{"label":"Analyze Invoices","id":"invoices","icon":"px-fea:templates"}]}]'
SELECTED_ROUTE = '["home"]'


class WebComponent(pn.pane.HTML):
    tag = param.String(TAG)
    items = param.String(ITEMS)
    selected_route = param.String(SELECTED_ROUTE)

    def __init__(self, **params):
        super().__init__(**params)

        self._set_html_tag()

    @param.depends("tag", "items", "selected_route", watch=True)
    def _update_object(self):
        self.object = f"""
        <{self.tag}
        items='{self.items}'
        selected-route='{self.selected_route}'
        </{self.tag}>
        """

    @param.depends("object", watch=True)
    def _update_parameters(self):
        NotImplementedError()
        # Extract tag items and selected_route from object
        # Maybe only extract selected_route

