# coding=utf-8
"""
    flask_resteasy.builders
    ~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import request


class ResponseBuilder(object):
    """Builds the JSON dictionary that is returned as a JSON response
    to client.
    """
    def __init__(self, cfg, request_processor):
        self._cfg = cfg
        self._rp = request_processor
        self._json_dic = None
        self._build()

    @property
    def json_dic(self):
        """JSON dictionary built for the processed resources and links.
        """
        return self._json_dic

    @property
    def urls(self):
        """Request URL for resource.
        """
        return self._get_urls_for(self._rp.resources)

    def _build(self):
        json_dic = {self._rp.resource_name: []
                    if self._rp.render_as_list else {}}

        if self._rp.render_as_list:
            for resource in self._rp.resources:
                json_dic[self._rp.resource_name].append(
                    self._resource_to_jdic(resource))
        else:
            if len(self._rp.resources) > 0:
                json_dic[self._rp.resource_name] = self._resource_to_jdic(
                    self._rp.resources[0])

        self._build_includes(json_dic)
        self._json_dic = json_dic

    def _build_includes(self, json_dic):

        for link in self._rp.links:
            link_key = self._cfg.json_case(link)
            if self._cfg.use_link_nodes:
                json_dic[self._cfg.linked_node] = {}
                json_dic[self._cfg.linked_node][link_key] = []
            else:
                json_dic[link_key] = []

            # switch cfg temporarily to the link object's configuration
            # this is borderline hackish
            parent_cfg = self._cfg
            try:
                self._cfg = self._cfg.api_manager.get_cfg(
                    self._cfg.resource_name_case(link))
                ids_processed = set()
                for link_obj in self._rp.links[link]:
                    if isinstance(link_obj, list):
                        for obj in link_obj:
                            self._build_linked_obj(obj, link_key,
                                                   ids_processed, json_dic)
                    else:
                        self._build_linked_obj(link_obj, link_key,
                                               ids_processed, json_dic)
            finally:
                self._cfg = parent_cfg

    def _build_linked_obj(self, obj, link_key, ids_processed, json_dic):
        ident = getattr(obj, self._cfg.id_field)
        if ident not in ids_processed:
            d = self._resource_to_jdic(obj)
            if self._cfg.use_link_nodes:
                json_dic[self._cfg.linked_node][link_key].append(d)
            else:
                json_dic[link_key].append(d)
            ids_processed.add(ident)

    def _resource_to_jdic(self, resource):
        dic = self._resource_fields_to_jdic(resource)
        dic.update(self._links_to_jdic(resource))
        return dic

    def _resource_fields_to_jdic(self, resource):
        dic = {}
        convert = self._cfg.model_to_json_type_converters
        if resource is not None:
            for field_name in self._cfg.allowed_from_model:
                fld_jkey = self._cfg.json_case(field_name)
                v = getattr(resource, field_name)
                current_type = self._cfg.field_types[field_name]
                if current_type in convert and v is not None:
                    dic[fld_jkey] = convert[current_type](v)
                else:
                    dic[fld_jkey] = v
        return dic

    def _links_to_jdic(self, resource):
        dic = {}
        if resource is not None:
            link_names = self._cfg.allowed_relationships
            dic = {}
            for link_name in link_names:
                link_jkey = self._cfg.json_case(link_name)
                link_obj = getattr(resource, link_name)
                if isinstance(link_obj, list):
                    ids = []
                    for link in link_obj:
                        ids.append(getattr(link, self._cfg.id_field))
                    self._set_link_jnode(dic, link_jkey, ids)
                else:
                    if link_obj is not None:
                        self._set_link_jnode(
                            dic, link_jkey,
                            getattr(link_obj, self._cfg.id_field))
                    else:
                        self._set_link_jnode(dic, link_jkey, None)
        return dic

    def _set_link_jnode(self, dic, link_jkey, link):
        if self._cfg.use_link_nodes:
            if self._cfg.links_node not in dic:
                dic[self._cfg.links_node] = {}
            dic[self._cfg.links_node][link_jkey] = link
        else:
            dic[link_jkey] = link

    @staticmethod
    def _get_urls_for(resources):
        urls = []
        if isinstance(resources, list):
            for resource in resources:
                urls.append('%s/%d' % (request.url, resource.id))
        else:
            urls.append('%s/%d' % (request.url, resources.id))
        return urls
