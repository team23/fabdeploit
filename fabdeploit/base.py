class BaseCommandUtil(object):
    def __init__(self, *kwargs):
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise RuntimeError('Unknown key {key}'.format(key=key))
