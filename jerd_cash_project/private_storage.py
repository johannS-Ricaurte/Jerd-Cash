from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateMediaStorage(FileSystemStorage):

    def __init__(self, *args, **kwargs):

        kwargs.setdefault(
            'location',
            settings.PRIVATE_MEDIA_ROOT
        )

        super().__init__(*args, **kwargs)

    def url(self, name):

        raise ValueError(
            "Este archivo es privado y no tiene una URL pública."
        )