# coding=utf-8
from flask import request

from .constants import LINKS_NODE


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
        return self._get_urls_for(self._rp.results)

    def _build(self):
        json_dic = {self._rp.root_name: [] if self._rp.render_as_list else {}}

        if self._rp.render_as_list:
            for model in self._rp.results:
                json_dic[self._rp.root_name].append(self._obj_to_dic(model))
        else:
            if len(self._rp.results) > 0:
                json_dic[self._rp.root_name] = self._obj_to_dic(
                    self._rp.results[0])

        self._json_dic = json_dic

    def _obj_to_dic(self, obj):
        dic = self._obj_fields_to_dic(obj)
        dic.update(self._obj_links_to_dic(obj))
        return dic

    def _obj_fields_to_dic(self, obj):
        dic = {}
        convert = self._cfg.to_json_converters
        if obj is not None:
            for field_name in self._cfg.fields_to_json:
                field_name_key = self._cfg.to_json_node(field_name)
                v = getattr(obj, field_name)
                current_type = self._cfg.field_types[field_name]
                if current_type in convert and v is not None:
                    dic[field_name_key] = convert[current_type](v)
                else:
                    dic[field_name_key] = v
        return dic

    def _set_link(self, dic, link_key, link_obj):
        if self._cfg.use_link_nodes:
            if LINKS_NODE not in dic:
                dic[LINKS_NODE] = {}
            dic[LINKS_NODE][link_key] = link_obj
        else:
            dic[link_key] = link_obj

    def _obj_links_to_dic(self, obj):
        dic = {}
        if obj is not None:
            links = self._cfg.relationships
            dic = {}
            for link in links:
                link_key = self._cfg.to_json_node(link)
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


class BuilderFactory(object):
    @staticmethod
    def create(cfg, response_builder):
        return ResponseBuilder(cfg, response_builder)