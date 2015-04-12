# coding=utf-8
"""
    flask_resteasy.errors
    ~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import jsonify


class UnableToProcess(Exception):
    """Exception raised for all error conditions
    Copied and adpated
    from: http://flask.pocoo.org/docs/0.10/patterns/apierrors/
    """
    status_code = 400

    def __init__(self, title, detail, status_code=None, payload=None):
        Exception.__init__(self)
        self.title = title
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Return exception info as a dictionary
        """
        er = {'title': self.title,
              'detail': self.detail,
              'status': self.status_code}
        er.update(self.payload or {})
        return {'errors': [er]}


def handle_errors(error):
    """Error handler that creates the json error response
    :param error: Exception being handled
    """
    if isinstance(error, UnableToProcess):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
    else:
        response = jsonify({'message': 'Unknown error %s' % error})
    return response
