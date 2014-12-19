# coding=utf-8
"""
    flask_resteasy.builders
    ~~~~~~~~~~~~~~

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
        return self._get_urls_for(self._rp.parents)

    def _build(self):
        json_dic = {self._rp.root_name: [] if self._rp.render_as_list else {}}

        if self._rp.render_as_list:
            for model in self._rp.parents:
                json_dic[self._rp.root_name].append(self._obj_to_dic(model))
        else:
            if len(self._rp.parents) > 0:
                json_dic[self._rp.root_name] = self._obj_to_dic(
                    self._rp.parents[0])

        for link in self._rp.includes:
            use_links = self._cfg.use_link_nodes
            # switch cfg temporarily to the link object's configuration
            # this is borderline hackish
            parent_cfg = self._cfg
            try:
                self._cfg = self._cfg.api_manager.get_cfg(link)
                for obj in self._rp.includes[link]:
                    rv = self._obj_to_dic(obj)
                    if use_links:
                        if self._cfg.linked_node not in json_dic:
                            json_dic[self._cfg.linked_node] = {}
                        json_dic[self._cfg.linked_node][link] = rv
                    else:
                        json_dic[link] = rv
            finally:
                self._cfg = parent_cfg

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
            if self._cfg.links_node not in dic:
                dic[self._cfg.links_node] = {}
            dic[self._cfg.links_node][link_key] = link_obj
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
