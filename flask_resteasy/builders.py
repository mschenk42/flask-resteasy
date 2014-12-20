# coding=utf-8
"""
    flask_resteasy.builders
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2014 by Michael Schenk.
    :license: BSD, see LICENSE for more details.
"""
from flask import request


class ResponseBuilder(object):
    def __init__(self, cfg, request_processor):
        self._cfg = cfg
        self._rp = request_processor
        self._json_dic = None
        self._build()

    @property
    def json_dic(self):
        return self._json_dic

    @property
    def urls(self):
        return self._get_urls_for(self._rp.resource_objs)

    def _build(self):
        json_dic = {self._rp.root_name: [] if self._rp.render_as_list else {}}

        if self._rp.render_as_list:
            for model in self._rp.resource_objs:
                json_dic[self._rp.root_name].append(self._obj_to_dic(model))
        else:
            if len(self._rp.resource_objs) > 0:
                json_dic[self._rp.root_name] = self._obj_to_dic(
                    self._rp.resource_objs[0])

        self._build_includes(json_dic)
        self._json_dic = json_dic

    def _build_includes(self, json_dic):

        def _build_linked_obj(lo, ids_p):
            ident = getattr(lo, self._cfg.id_field)
            if ident not in ids_p:
                d = self._obj_to_dic(lo)
                if use_links:
                    json_dic[self._cfg.linked_node][link].append(d)
                else:
                    json_dic[link].append(d)
                ids_p.add(ident)

        for link in self._rp.linked_objs:
            use_links = self._cfg.use_link_nodes
            if use_links:
                json_dic[self._cfg.linked_node] = {}
                json_dic[self._cfg.linked_node][link] = []
            else:
                json_dic[link] = []

            # switch cfg temporarily to the link object's configuration
            # this is borderline hackish
            parent_cfg = self._cfg
            try:
                self._cfg = self._cfg.api_manager.get_cfg(link)
                ids_processed = set()
                for obj in self._rp.linked_objs[link]:
                    if isinstance(obj, list):
                        for o in obj:
                            _build_linked_obj(o, ids_processed)
                    else:
                        _build_linked_obj(obj, ids_processed)
            finally:
                self._cfg = parent_cfg

    def _obj_to_dic(self, obj):
        dic = self._obj_fields_to_dic(obj)
        dic.update(self._obj_links_to_dic(obj))
        return dic

    def _obj_fields_to_dic(self, obj):
        dic = {}
        convert = self._cfg.model_to_json_type_converters
        if obj is not None:
            for field_name in self._cfg.allowed_from_model:
                field_name_key = self._cfg.json_node_case(field_name)
                v = getattr(obj, field_name)
                current_type = self._cfg.field_types[field_name]
                if current_type in convert and v is not None:
                    dic[field_name_key] = convert[current_type](v)
                else:
                    dic[field_name_key] = v
        return dic

    def _set_link(self, dic, link_key, link_obj):
        if self._cfg.use_link_nodes:
            if self._cfg.links_node not in dic:
                dic[self._cfg.links_node] = {}
            dic[self._cfg.links_node][link_key] = link_obj
        else:
            dic[link_key] = link_obj

    def _obj_links_to_dic(self, obj):
        dic = {}
        if obj is not None:
            links = self._cfg.allowed_relationships
            dic = {}
            for link in links:
                link_key = self._cfg.json_node_case(link)
                linked_obj = getattr(obj, link)
                if isinstance(linked_obj, list):
                    l_lst = []
                    for l_item in linked_obj:
                        l_lst.append(getattr(l_item, self._cfg.id_field))
                    self._set_link(dic, link_key, l_lst)
                else:
                    if linked_obj:
                        self._set_link(dic, link_key,
                                       getattr(linked_obj,
                                               self._cfg.id_field))
                    else:
                        self._set_link(dic, link_key, None)
        return dic

    @staticmethod
    def _get_urls_for(objs):
        urls = []
        if isinstance(objs, list):
            for o in objs:
                urls.append('%s/%d' % (request.url, o.id))
        else:
            urls.append('%s/%d' % (request.url, objs.id))
        return urls
