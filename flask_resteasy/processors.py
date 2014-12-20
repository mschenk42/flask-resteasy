# coding=utf-8
"""
    flask_resteasy.processors
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Copyright 2014 Michael Schenk

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
    see LICENSE file for more details

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
from abc import abstractmethod
from flask import request
from inflection import pluralize


class RequestProcessor(object):
    def __init__(self, cfg, request_parser):
        self._cfg = cfg
        self._rp = request_parser
        self._parents = []
        self._includes = {}
        self._render_as_list = False
        self._process()

    @abstractmethod
    def _process(self):
        pass

    @property
    def resource_objs(self):
        return self._parents

    @property
    def render_as_list(self):
        return self._render_as_list

    @property
    def linked_objs(self):
        return self._includes

    @property
    def root_name(self):
        if self._rp.link is None:
            return (self._cfg.resource_name_plural
                    if self._render_as_list else self._cfg.resource_name)
        else:
            return self._rp.link

    def _build_query(self, model_class):
        query = model_class.query
        if self._rp.filter:
            query = query.filter_by(**self._rp.filter)
        if self._rp.sort_by:
            for col, order in self._rp.sort_by.items():
                fld = getattr(getattr(model_class, col), order)()
                query = query.order_by(fld)
        return query

    def _all(self, model_class=None):
        if model_class is None:
            model_class = self._cfg.model_class
        else:
            model_class = model_class
        return self._build_query(model_class).all()

    def _get_all(self, idents, model_class=None):
        models = []
        if model_class is None:
            model_class = self._cfg.model_class
        else:
            model_class = model_class
        for i in idents:
            models.append(self._get_or_404(i, model_class))
        return models

    def _get_or_404(self, ident, model_class=None):
        if model_class is None:
            model_class = self._cfg.model_class
        else:
            model_class = model_class
        return model_class.query.get_or_404(ident)

    def _copy(self, model, fields, field_defaults=None, model_class=None):
        if model_class is None:
            model_class = self._cfg.model_class
        else:
            model_class = model_class
        field_defaults = field_defaults if field_defaults else {}
        model_copy = model_class()
        for field in fields:
            setattr(model_copy, field, field_defaults[field]
                    if field in field_defaults else getattr(model, field))
        return model_copy

    def _copy_models(self, models, fields, field_defaults=None,
                     model_class=None):
        model_copies = []
        for model in models:
            model_copies.append(
                self._copy(model, fields, field_defaults, model_class))
        return model_copies

    def _json_to_model(self, j_dict, model):

        def _json_to_model_fields(j_dict_root):
            for c in self._cfg.fields_to_model:
                if c in j_dict_root:
                    setattr(model, c, j_dict_root[c])

        def _json_to_model_links(j_dict_links):
            for c in self._cfg.relationships:
                if c in j_dict_links:
                    model_link = j_dict_links[c]
                    if model_link is None:
                        continue
                    elif isinstance(model_link, list):
                        lst = self._get_all(
                            model_link,
                            self._cfg.api_manager.get_model(c))
                        getattr(model, c).extend(lst)
                    else:
                        setattr(model, c,
                                self._get_or_404(
                                    model_link,
                                    self._cfg.api_manager.get_model(c)))

        for root in j_dict:
            _json_to_model_fields(j_dict[root])
            if self._cfg.use_link_nodes:
                if self._cfg.links_node in j_dict[root]:
                    _json_to_model_links(j_dict[root][self._cfg.links_node])
                else:
                    _json_to_model_links(j_dict[root])
            else:
                _json_to_model_links(j_dict[root])


class GetRequestProcessor(RequestProcessor):
    def __init__(self, cfg, request_parser):
        super(GetRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        if len(self._rp.idents) > 0:
            r_objs = self._get_all(self._rp.idents)
        else:
            r_objs = self._all()

        if self._rp.link:
            assert len(r_objs) > 0, 'No parent resource found for links'
            for r_o in r_objs:
                l_objs = getattr(r_o, self._cfg.to_model_field(self._rp.link))
                self._render_as_list = isinstance(l_objs, list)
                if self._render_as_list:
                    self._parents.extend(l_objs)
                else:
                    self._parents.append(l_objs)
                self._process_includes_for(l_objs)
        else:
            self._process_includes_for(r_objs)
            self._render_as_list = len(self._rp.idents) != 1
            self._parents.extend(r_objs)

    def _process_includes_for(self, obj):
        # todo add to config ability to exclude relationships in config?

        def set_include(parent_obj, include):
            if hasattr(parent_obj, include):
                k = pluralize(include)
                if k not in self._includes:
                    self._includes[k] = []
                self._includes[k].append(getattr(parent_obj, include))

        if self._rp.include:
            for include in self._rp.include:
                if include not in self._cfg.relationships:
                    continue
                if isinstance(obj, list):
                    for o in obj:
                        set_include(o, include)
                else:
                    set_include(obj, include)


class DeleteRequestProcessor(RequestProcessor):
    def __init__(self, cfg, request_parser):
        super(DeleteRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        for i in self._rp.idents:
            obj = self._get_or_404(i)
            self._cfg.db.session.delete(obj)
        self._cfg.db.session.commit()


class PostRequestProcessor(RequestProcessor):
    def __init__(self, cfg, request_parser):
        super(PostRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        # todo - handle creating many models per post
        json = request.json
        with self._cfg.db.session.no_autoflush:
            model = self._cfg.model_class()
            self._json_to_model(json, model)
        self._cfg.db.session.commit()
        self._parents.append(model)


class PutRequestProcessor(RequestProcessor):
    def __init__(self, cfg, request_parser):
        super(PutRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        # todo - handle updating many models per put
        json = request.json
        with self._cfg.db.session.no_autoflush:
            model = self._get_or_404(self._rp.idents[0])
            self._json_to_model(json, model)
        self._cfg.db.session.commit()
        self.resource_objs.append(model)
