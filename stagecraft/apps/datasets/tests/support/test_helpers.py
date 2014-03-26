import json

from hamcrest.core.base_matcher import BaseMatcher


class IsResponseWithHeader(BaseMatcher):
    def __init__(self, expected_header, expected_value):
        self.expected_header = expected_header
        self.expected_value = expected_value

    def _matches(self, response):
        return response.get(self.expected_header) == self.expected_value

    def describe_to(self, description):
        description.append_text(
            "response with header {} of {}".format(
                self.expected_header, self.expected_value))


def has_header(header, value):
    return IsResponseWithHeader(header, value)


class IsResponseWithStatus(BaseMatcher):
    def __init__(self, expected_status):
        self.expected_status = expected_status

    def _matches(self, response):
        return response.status_code == self.expected_status

    def describe_to(self, description):
        description.append_text(
            "response with status code %d" % self.expected_status)


def has_status(status_code):
    return IsResponseWithStatus(status_code)


def is_unauthorized():
    return has_status(403)


class IsErrorResponse(BaseMatcher):
    def _matches(self, response):
        try:
            data = json.loads(response.content.decode("utf-8"))
            if data.get('status') != 'error':
                return False
            # it should not fail with out a message
            if not data.get('message'):
                return False
            return True
        except ValueError:
            return False

    def describe_to(self, description):
        description.append_text(
            'error response'
        )


def is_error_response():
    return IsErrorResponse()
