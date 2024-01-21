from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database.db import get_db
from src.database.models import User, Publication, Rating
from src.repositories import publications as repositories_publications
from src.repositories import ratings as repositories_ratings
from src.schemas.ratings import RatingCreate, RatingResponse
from src.services.auth import auth_service
from src.utils.my_logger import logger
import src.messages as msg

router = APIRouter(prefix='/publications', tags=['grades'])


@router.post('/{publication_id}/rating/add', status_code=status.HTTP_201_CREATED, response_model=RatingResponse)
async def add_rating(publication_id: int, body: RatingCreate, db: AsyncSession = Depends(get_db),
                     user: User = Depends(auth_service.get_current_user)):

    publication = await repositories_publications.get_publication_by_id(publication_id, db)
    if publication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg.PUBLICATION_NOT_FOUND)

    if user.id == publication.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg.OWN_PUBLICATION)

    try:
        rating = await repositories_ratings.add_rating(publication_id, body, db, user)
        return rating
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg.ALREADY_VOTED_PUBLICATION)
