# -*- coding: utf-8 -*-
"""
Endpoints de autenticación para la API.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.services.auth import auth_service
from src.core.database import get_db_session
from src.core.security import create_access_token
from config.settings import settings
from src.schemas.token import Token

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Endpoint para obtener un token de acceso JWT.
    """
    user = await auth_service.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id)
    # Establecer cookie HttpOnly para sesiones basadas en cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=(settings.PROJECT_VERSION != "development"),
        samesite="strict",
        max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return {"access_token": access_token, "token_type": "bearer"}
