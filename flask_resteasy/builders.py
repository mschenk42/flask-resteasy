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
        self._processor = request_processor
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
        return self._get_urls_for(self._processor.resources)

    def _build(self):
        """Builds the json dictionary to be used for creating the
        json response.
        """
        json_dic = {self._processor.resource_name: []}
        num_resc = len(self._processor.resources)
        if num_resc > 0:
            if self._processor.render_as_list:
                # What with the render_as_list property?
                # Why don't we just render as a list if there is more than
                # one item? Because the client may expect a list even if there
                # is only one item. This is determined by the processor.  See
                # GetRequestProcessor.
                for resource in self._processor.resources:
                    json_dic[self._processor.resource_name].append(
                        self._resource_to_jdic(resource))
            else:
                assert num_resc == 1, 'Unexpected number of results'
                json_dic[self._processor.resource_name] = \
                    self._resource_to_jdic(self._processor.resources[0])

            self._build_includes(json_dic)
            self._build_pagination(json_dic)

        self._json_dic = json_dic

    def _resource_to_jdic(self, resource):
        """Build dictionary for resource objects and their
        links (relationships)
        """
        rv = self._resource_fields_to_jdic(resource)
        rv.update(self._links_to_jdic(resource))
        return rv

    def _resource_fields_to_jdic(self, resource):
        """Copy allowed resource fields to the dictionary
        """
        rv = {}
        convert = self._cfg.model_to_json_type_converters
        for field_name in self._cfg.allowed_from_model:
            fld_jkey = self._cfg.json_case(field_name)
            v = getattr(resource, field_name)
            current_type = self._cfg.field_types[field_name]
            if current_type in convert and v is not None:
                rv[fld_jkey] = convert[current_type](v)
            else:
                rv[fld_jkey] = v
        return rv

    def _links_to_jdic(self, resource):
        """Copy allowed links (relationships) for the resource object
        to the dictionary
        """
        rv = {}
        link_names = self._cfg.allowed_relationships
        rv = {}
        for link_name in link_names:
            link_jkey = self._cfg.json_case(link_name)
            link_obj = getattr(resource, link_name)
            if isinstance(link_obj, list):
                ids = []
                for link in link_obj:
                    ids.append(getattr(link, self._cfg.id_field))
                self._set_link_jnode(rv, link_jkey, ids)
            else:
                if link_obj is not None:
                    self._set_link_jnode(
                        rv, link_jkey,
                        getattr(link_obj, self._cfg.id_field))
                else:
                    self._set_link_jnode(rv, link_jkey, None)
        return rv

    def _set_link_jnode(self, dic, link_jkey, link):
        """Helper method for setting a link node
        """
        if self._cfg.use_link_nodes:
            if self._cfg.links_node not in dic:
                dic[self._cfg.links_node] = {}
            dic[self._cfg.links_node][link_jkey] = link
        else:
            dic[link_jkey] = link

    def _build_includes(self, json_dic):
        """Process includes (side-loaded links)
        """
        for link in self._processor.links:
            link_key = self._cfg.json_case(link)
            if self._cfg.use_link_nodes:
                if self._cfg.linked_node not in json_dic:
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
                for link_obj in self._processor.links[link]:
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
        """Helper method to build dictionary for linked objects
        """
        ident = getattr(obj, self._cfg.id_field)
        if ident not in ids_processed:
            d = self._resource_to_jdic(obj)
            if self._cfg.use_link_nodes:
                json_dic[self._cfg.linked_node][link_key].append(d)
            else:
                json_dic[link_key].append(d)
            ids_processed.add(ident)

    def _build_pagination(self, json_dic):
        """Set meta node if this response is paginated
        """
        rp = self._processor
        if rp.pager and rp.pager.should_return_meta:
            json_dic['meta'] = {rp.pager.page_no_param: rp.pager.page,
                                rp.pager.no_pages_param: rp.pager.no_pages,
                                rp.pager.per_page_param: rp.pager.per_page}

    @staticmethod
    def _get_urls_for(resources):
        """For a resource return it urls for each id
        """
        if isinstance(resources, list):
            rv = ['%s/%s' % (request.url, r.id) for r in resources]
        else:
            rv = [('%s/%s' % (request.url, resources.id))]
        return rv