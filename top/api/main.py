# Copyright 2021 - 2023 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing the main FastAPI router and API endpoints."""

from fastapi import FastAPI, HTTPException, Response, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ghga_service_commons.api import configure_app

from ..config import CONFIG
from ..core.models import LoginInfo, UserInfo
from ..core.oidc_provider import OidcProvider

app = FastAPI()
configure_app(app, config=CONFIG)

oidc_provider = OidcProvider(CONFIG)

tags = ["TestOP"]


@app.get(
    "/health",
    summary="health",
    tags=tags,  # pyright: ignore
    status_code=200,
)
async def health():
    """Used to test if this service is alive"""
    return {"status": "OK"}


@app.post(
    "/login",
    summary="Log in as a test user",
    tags=tags,  # pyright: ignore
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": str,
            "description": "Access token has been created.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error in submitted data."
        },
    },
)
async def login(login_info: LoginInfo) -> Response:
    """The UserInfo endpoint of the test OP."""
    try:
        token = oidc_provider.login(login_info)
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        ) from error
    return Response(
        content=token, media_type="application/jwt", status_code=status.HTTP_201_CREATED
    )


@app.get(
    "/userinfo",
    summary="Get user information",
    tags=tags,  # pyright: ignore
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": UserInfo,
            "description": "User info has been fetched.",
        },
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized to get user info."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error in submitted data."
        },
    },
)
async def get_userinfo(
    credentials: HTTPAuthorizationCredentials = Security(HTTPBearer()),
) -> UserInfo:
    """The UserInfo endpoint of the test OP."""
    token = credentials.credentials
    try:
        return oidc_provider.user_info(token)
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        ) from error
