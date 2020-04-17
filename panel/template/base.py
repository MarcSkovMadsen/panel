"""
Templates allow multiple Panel objects to be embedded into custom HTML
documents.
"""
from __future__ import absolute_import, division, unicode_literals

import pathlib
import sys
import uuid

from functools import partial

import param

from bokeh.document.document import Document as _Document
from bokeh.io import curdoc as _curdoc
from jinja2.environment import Template as _Template
from six import string_types
from pyviz_comms import JupyterCommManager as _JupyterCommManager

from ..config import config, panel_extension
from ..io.model import add_to_doc
from ..io.notebook import render_template
from ..io.save import save
from ..io.state import state
from ..layout import Card, Column, ListLike
from ..models.comm_manager import CommManager
from ..pane import panel as _panel, HTML, Str, HoloViews
from ..viewable import ServableMixin, Viewable
from ..widgets import Button

_server_info = (
    '<b>Running server:</b> <a target="_blank" href="https://localhost:{port}">'
    'https://localhost:{port}</a>')


class BaseTemplate(param.Parameterized, ServableMixin):

    # Dictionary of property overrides by bokeh Model type
    _modifiers = {}
    
    __abstract = True

    def __init__(self, template=None, items=None, nb_template=None, **params):
        super(BaseTemplate, self).__init__(**params)
        if isinstance(template, string_types):
            self._code = template
            template = _Template(template)
        else:
            self._code = None
        self.template = template
        if isinstance(nb_template, string_types):
            nb_template = _Template(nb_template)
        self.nb_template = nb_template or template
        self._render_items = {}
        self._render_variables = {}
        self._server = None
        self._layout = self._build_layout()

    def _build_layout(self):
        str_repr = Str(repr(self))
        server_info = HTML('')
        button = Button(name='Launch server')
        def launch(event):
            if self._server:
                button.name = 'Launch server'
                server_info.object = ''
                self._server.stop()
                self._server = None
            else:
                button.name = 'Stop server'
                self._server = self._get_server(start=True, show=True)
                server_info.object = _server_info.format(port=self._server.port)
        button.param.watch(launch, 'clicks')
        return Column(str_repr, server_info, button)
    def __repr__(self):
        cls = type(self).__name__
        spacer = '\n    '
        objs = ['[%s] %s' % (name, obj[0].__repr__(1))
                for name, obj in self._render_items.items()
                if not name.startswith('_')]
        template = '{cls}{spacer}{objs}'
        return template.format(
            cls=cls, objs=('%s' % spacer).join(objs), spacer=spacer)

    def _apply_modifiers(self, viewable, mref):
        model, _ = viewable._models[mref]
        modifiers = self._modifiers.get(type(viewable), {})
        viewable.param.set_param(**{k: v for k, v in modifiers.items()
                                    if getattr(viewable, k) == viewable.param[k].default})

    def _init_doc(self, doc=None, comm=None, title=None, notebook=False, location=True):
        doc = doc or _curdoc()
        title = title or 'Panel Application'
        doc.title = title
        col = Column()
        preprocess_root = col.get_root(doc, comm)
        ref = preprocess_root.ref['id']
        for name, (obj, tags) in self._render_items.items():
            model = obj.get_root(doc, comm)
            mref = model.ref['id']
            doc.on_session_destroyed(obj._server_destroy)
            for sub in obj.select(Viewable):
                sub._models[ref] = sub._models.get(mref)
                if isinstance(sub, HoloViews) and mref in sub._plots:
                    sub._plots[ref] = sub._plots.get(mref)
            col.objects.append(obj)
            obj._documents[doc] = model
            model.name = name
            model.tags = tags
            for o in obj.select():
                self._apply_modifiers(o, mref)
            add_to_doc(model, doc, hold=bool(comm))

        state._fake_roots.append(ref)
        state._views[ref] = (col, preprocess_root, doc, comm)

        if location:
            from ..io.location import Location
            if isinstance(location, Location):
                loc = location
            elif doc in state._locations:
                loc = state.location
            else:
                loc = Location()
            state._locations[doc] = loc
            loc_model = loc._get_model(doc, preprocess_root)
            loc_model.name = 'location'
            #doc.add_root(loc_model)

        col._preprocess(preprocess_root)
        col._documents[doc] = preprocess_root
        doc.on_session_destroyed(col._server_destroy)

        if notebook:
            doc.template = self.nb_template
        else:
            doc.template = self.template
        doc._template_variables.update(self._render_variables)
        return doc

    def _repr_mimebundle_(self, include=None, exclude=None):
        loaded = panel_extension._loaded
        if not loaded and 'holoviews' in sys.modules:
            import holoviews as hv
            loaded = hv.extension._loaded
        if not loaded:
            param.main.warning('Displaying Panel objects in the notebook '
                               'requires the panel extension to be loaded. '
                               'Ensure you run pn.extension() before '
                               'displaying objects in the notebook.')
            return None

        try:
            assert get_ipython().kernel is not None # noqa
            state._comm_manager = _JupyterCommManager
        except Exception:
            pass

        from IPython.display import display

        doc = _Document()
        comm = state._comm_manager.get_server_comm()
        self._init_doc(doc, comm, notebook=True)
        ref = doc.roots[0].ref['id']
        manager = CommManager(
            comm_id=comm.id, plot_id=ref, name='comm_manager'
        )
        client_comm = state._comm_manager.get_client_comm(
            on_msg=partial(self._on_msg, ref, manager),
            on_error=partial(self._on_error, ref),
            on_stdout=partial(self._on_stdout, ref)
        )
        manager.client_comm_id = client_comm.id
        doc.add_root(manager)

        if config.console_output != 'disable':
            handle = display(display_id=uuid.uuid4().hex)
            state._handles[ref] = (handle, [])

        return render_template(doc, comm, manager)

    def save(self, filename, title=None, resources=None, embed=False,
             max_states=1000, max_opts=3, embed_json=False,
             json_prefix='', save_path='./', load_path=None):
        """
        Saves Panel objects to file.

        Arguments
        ---------
        filename: string or file-like object
           Filename to save the plot to
        title: string
           Optional title for the plot
        resources: bokeh resources
           One of the valid bokeh.resources (e.g. CDN or INLINE)
        embed: bool
           Whether the state space should be embedded in the saved file.
        max_states: int
           The maximum number of states to embed
        max_opts: int
           The maximum number of states for a single widget
        embed_json: boolean (default=True)
           Whether to export the data to json files
        json_prefix: str (default='')
           Prefix for the auto-generated json directory
        save_path: str (default='./')
           The path to save json files to
        load_path: str (default=None)
           The path or URL the json files will be loaded from.
        """
        if embed:
            raise ValueError("Embedding is not yet supported on Template.")
        return save(self, filename, title, resources, self.template,
                    self._render_variables, embed, max_states, max_opts,
                    embed_json, json_prefix, save_path, load_path)

    def server_doc(self, doc=None, title=None, location=True):
        """
        Returns a servable bokeh Document with the panel attached

        Arguments
        ---------
        doc : bokeh.Document (optional)
          The Bokeh Document to attach the panel to as a root,
          defaults to bokeh.io.curdoc()
        title : str
          A string title to give the Document
        location : boolean or panel.io.location.Location
          Whether to create a Location component to observe and
          set the URL location.

        Returns
        -------
        doc : bokeh.Document
          The Bokeh document the panel was attached to
        """
        return self._init_doc(doc, title=title, location=location)

    def select(self, selector=None):
        """
        Iterates over the Template and any potential children in the
        applying the Selector.

        Arguments
        ---------
        selector: type or callable or None
          The selector allows selecting a subset of Viewables by
          declaring a type or callable function to filter by.

        Returns
        -------
        viewables: list(Viewable)
        """
        objects = []
        for obj, _ in self._render_items.values():
            objects += obj.select(selector)
        return objects



class BasicTemplate(BaseTemplate):
    """
    BasicTemplate provides a baseclass for templates with a basic
    organization including a header, sidebar and main area.
    """

    header = param.ClassSelector(class_=ListLike, constant=True)

    main = param.ClassSelector(class_=ListLike, constant=True)

    sidebar = param.ClassSelector(class_=ListLike, constant=True)

    title = param.String()

    _css = None

    _template = None

    _modifiers = {}

    __abstract = True

    def __init__(self, **params):
        if self._css and self._css not in config.css_files:

            config.css_files.append(self._css)
        template = self._template.read_text()
        header = ListLike()
        main = ListLike()
        sidebar = ListLike()
        super(BasicTemplate, self).__init__(
            template, main=main, sidebar=sidebar, header=header, **params
        )
        self._render_variables['app_title'] = self.title
        self.main.param.watch(self._update_render_items, ['objects'])
        self.sidebar.param.watch(self._update_render_items, ['objects'])
        self.header.param.watch(self._update_render_items, ['objects'])
        self.param.watch(self._update_title, ['title'])

    def _update_title(self, event):
        self._render_variables['app_title'] = event.new

    def _update_render_items(self, event):
        if event.obj is self.main:
            tag = 'main'
        elif event.obj is self.sidebar:
            tag = 'nav'
        elif event.obj is self.header:
            tag = 'header'
        for obj in event.old:
            ref = obj.name
            if obj not in event.new and ref in self._render_items:
                del self._render_items[ref]
        for obj in event.new:
            ref = obj.name
            if ref not in self._render_items:
                self._render_items[ref] = (obj, [tag])
        tags = [tags for _, tags in self._render_items.values()]
        self._render_variables['nav'] = any('nav' in ts for ts in tags)
        self._render_variables['header'] = any('header' in ts for ts in tags)



class Template(BaseTemplate):
    """
    A Template is a high-level component to render multiple Panel
    objects into a single HTML document defined through a Jinja2
    template. The Template object is given a Jinja2 template and then
    allows populating this template by adding Panel objects, which are
    given unique names. These unique names may then be referenced in
    the template to insert the rendered Panel object at a specific
    location. For instance, given a Jinja2 template that defines roots
    A and B like this:

        <div> {{ embed(roots.A) }} </div>
        <div> {{ embed(roots.B) }} </div>

    We can then populate the template by adding panel 'A' and 'B' to
    the Template object:

        template.add_panel('A', pn.panel('A'))
        template.add_panel('B', pn.panel('B'))

    Once a template has been fully populated it can be rendered using
    the same API as other Panel objects. Note that all roots that have
    been declared using the {{ embed(roots.A) }} syntax in the Jinja2
    template must be defined when rendered.

    Since embedding complex CSS frameworks inside a notebook can have
    undesirable side-effects and a notebook does not afford the same
    amount of screen space a Template may given separate template
    and nb_template objects. This allows for different layouts when
    served as a standalone server and when used in the notebook.
    """

    def __init__(self, template=None, nb_template=None, items=None, **params):
        super(Template, self).__init__(template, nb_template, **params)
        items = {} if items is None else items
        for name, item in items.items():
            self.add_panel(name, item)

    #----------------------------------------------------------------
    # Public API
    #----------------------------------------------------------------

    def add_panel(self, name, panel, tags=[]):
        """
        Add panels to the Template, which may then be referenced by
        the given name using the jinja2 embed macro.

        Arguments
        ---------
        name : str
          The name to refer to the panel by in the template
        panel : panel.Viewable
          A Panel component to embed in the template.
        """
        if name in self._render_items:
            raise ValueError('The name %s has already been used for '
                             'another panel. Ensure each panel '
                             'has a unique name by which it can be '
                             'referenced in the template.' % name)
        self._render_items[name] = (_panel(panel), tags)
        self._layout[0].object = repr(self)

    def add_variable(self, name, value):
        """
        Add parameters to the template, which may then be referenced
        by the given name in the Jinja2 template.

        Arguments
        ---------
        name : str
          The name to refer to the panel by in the template
        value : object
          Any valid Jinja2 variable type.
        """
        if name in self._render_variables:
            raise ValueError('The name %s has already been used for '
                             'another variable. Ensure each variable '
                             'has a unique name by which it can be '
                             'referenced in the template.' % name)
        self._render_variables[name] = value
