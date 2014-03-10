from logging import getLogger

logger = getLogger(__name__)


def extract_bearer_token(header):
    if header is None or len(header) < 8:
        return ''
        # Strip the leading "Bearer " from the header value
    return header[7:]
