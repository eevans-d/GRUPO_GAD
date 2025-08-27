# -*- coding: utf-8 -*-
"""
Esquemas para la autenticación y los tokens JWT.
"""

from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None
