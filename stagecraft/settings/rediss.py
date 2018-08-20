import os
# ssl is not unused...it's inside an eval
import ssl

if os.environ.get('STAGECRAFT_BROKER_SSL_CERT_REQS', False):
    BROKER_USE_SSL = {
        'ssl_cert_reqs': eval('ssl.{}'.format(os.environ['STAGECRAFT_BROKER_SSL_CERT_REQS']))
    }
