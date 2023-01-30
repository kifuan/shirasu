class SingletonMeta(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls._singleton_instance = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton_instance is None:
            cls._singleton_instance = super().__call__(*args, **kwargs)
        return cls._singleton_instance
