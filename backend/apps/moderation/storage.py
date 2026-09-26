from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateVerificationStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs["location"] = settings.PRIVATE_MEDIA_ROOT
        kwargs["base_url"] = None

        super().__init__(*args, **kwargs)


private_verification_storage = PrivateVerificationStorage()