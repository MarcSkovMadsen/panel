import param

import panel as pn


class WebComponent(pn.pane.HTML):
    tag = param.String(constant=True)
#     src = param.Tuple(constant=True)
#     attributes = (param.Tuple((), constant=True)
# )
#     @param.depends(*attributes)
#     def _update_object(self):
#         super.update()







# <vaadin-checkbox value="Option" checked>Option</vaadin-checkbox>
