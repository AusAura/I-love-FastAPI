from enum import Enum
from typing import BinaryIO, Any

import cloudinary
from cloudinary.api import delete_resources_by_prefix
from cloudinary.uploader import upload, destroy, rename
from cloudinary.exceptions import Error as CloudinaryError

from src.conf.config import config
from src.services.transformations import TRANSFORMATIONS
from src.utils.my_logger import logger
import src.messages as msg


class CloudinaryServiceError(Exception):
    """Основной класс для ошибок CloudinaryService."""

    def __init__(self, message: str, *args: Any) -> None:
        super().__init__(*args)
        self.message = message


class CloudinaryResourceNotFoundError(CloudinaryServiceError):
    def __init__(self, message: str, *args: Any) -> None:
        super().__init__(message, *args)


class PermissionsFolder(Enum):
    temp = "temp"
    publications = "publications"
    avatar = "avatar"

    @classmethod
    def array(cls) -> list[str]:
        return [field.name for field in cls]


class CloudinaryService:
    def __init__(self):
        cloudinary.config(
            cloud_name=config.CLOUDINARY_NAME,
            api_key=config.CLOUDINARY_API_KEY,
            api_secret=config.CLOUDINARY_API_SECRET,
        )

        self.command_transformation = TRANSFORMATIONS

    per_folder = PermissionsFolder

    def __call__(self):
        return self

    def get_cloud_id(self, email: str, postfix: str, post_id: int | None = None,
                     folder: str | None = None) -> str | None:

        if folder is None: folder = self.per_folder.temp.name

        if folder not in self.per_folder.array():
            raise CloudinaryServiceError(f"Folder '{folder}' not allowed")

        public_id = f"{email}/{folder}/{postfix}" if post_id is None else f"{email}/{folder}/{post_id}/{postfix}"

        try:
            cloudinary.api.resource(public_id)
            return public_id
        except CloudinaryError as err:
            if msg.CLOUD_RESOURCE_NOT_FOUND in str(err):
                return None
            raise CloudinaryServiceError(str(err))

    def save_by_email(self, data: BinaryIO | str, email: str, postfix: str, post_id: int | None = None,
                      folder: str | None = None) -> str:

        if folder is None: folder = self.per_folder.temp.name

        if folder not in self.per_folder.array():
            raise CloudinaryServiceError(f"Folder '{folder}' not allowed")

        public_id = f"{email}/{folder}/{postfix}" if post_id is None else f"{email}/{folder}/{post_id}/{postfix}"

        result = upload(data, public_id=public_id, overwrite=True)

        logger.info(f'upload image({folder}) from user: {email} id: {result["public_id"]}')
        return result['secure_url']

    def replace_temp_to_publications(self, email: str, postfix: str, post_id: int) -> dict[str, str]:

        from_public_id = f"{email}/{self.per_folder.temp.name}/{postfix}"
        to_public_id = f"{email}/{self.per_folder.publications.name}/{post_id}/{postfix}"

        if self.get_cloud_id(email, postfix):
            result = rename(from_public_id=from_public_id, to_public_id=to_public_id)
        else:
            return {postfix: None}

        return {postfix: result['secure_url']}

    def delete_by_email(self, email: str, post_id: int, folder: str, postfixes: list[str]) -> None:
        #  Delete all resources by post_id from user's cloudinary folder
        folder_path = f"{email}/{folder}/{post_id}"

        for postfix in postfixes:
            try:
                delete_resources_by_prefix(prefix=f"{folder_path}/{postfix}")
            except CloudinaryError as err:
                if msg.CLOUD_RESOURCE_NOT_FOUND in str(err):
                    continue
                raise CloudinaryServiceError(str(err))

        cloudinary.api.delete_folder(folder_path)

    def apply_transformation(self, key: str, email: str, current_postfix: str, updated_postfix: str,
                             post_id: int | None = None, folder: str | None = None) -> str:

        if key not in self.command_transformation:
            raise CloudinaryServiceError(f"Invalid transformation key: {key}")

        if (cloud_id := self.get_cloud_id(email=email, post_id=post_id, folder=folder, postfix=updated_postfix)) is None:
            if (cloud_id := self.get_cloud_id(email=email, post_id=post_id, folder=folder, postfix=current_postfix)) is None:
                raise CloudinaryResourceNotFoundError(msg.CLOUD_RESOURCE_NOT_FOUND)

        # Build the URL with the specified transformation
        transformed_url = cloudinary.CloudinaryImage(cloud_id).build_url(**self.command_transformation.get(key))

        # Create a new public ID for the transformed image
        logger.info(f'upload image(transformed) from user: {cloud_id}')
        # Upload the transformed image as a new asset with the new public ID
        transformed_url = self.save_by_email(transformed_url, email, updated_postfix, post_id, folder)

        return transformed_url


cloud_img_service = CloudinaryService()

TRANSFORMATION_KEYS = cloud_img_service.command_transformation.keys()
