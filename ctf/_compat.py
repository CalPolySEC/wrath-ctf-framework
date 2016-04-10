text_type = type(u'')


def want_bytes(s, encoding='utf-8'):
    if isinstance(s, text_type):
        s = s.encode(encoding)
    return s
