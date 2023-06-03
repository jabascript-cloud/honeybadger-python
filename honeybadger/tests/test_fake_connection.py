from honeybadger.fake_connection import send_notice

from testfixtures import log_capture


@log_capture()
def test_send_notice_logging(log):
    config = {'api_key': 'aaa'}
    payload = {'test': 'payload', 'error': {'token': '1234'}}

    send_notice(config, payload)

    log.check(
        ('honeybadger.fake_connection', 'INFO',
         'Development mode is enabled; this error will be reported if it occurs after you deploy your app.'),
        ('honeybadger.fake_connection', 'DEBUG', 'The config used is {} with payload {}'.format(config, payload)))
