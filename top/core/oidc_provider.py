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
#

"""Test OpenID Connect provider"""

from __future__ import annotations

import asyncio
from typing import Any

from ghga_service_commons.utils.jwt_helpers import (
    decode_and_validate_token,
    generate_jwk,
    sign_and_serialize_token,
)
from jwcrypto import jwk
from pydantic import AnyHttpUrl, BaseSettings, Field

from .models import UserInfo

__all__ = ["OidcProviderConfig", "OidcProvider"]


class OidcProviderConfig(BaseSettings):
    """The configuration for a test OpenID Connect provider."""

    issuer: AnyHttpUrl = Field("https://test-op.org", description="test issuer URL")
    user_domain: str = Field(
        "home.org", description="domain name of the home organization of the test users"
    )
    client_id: str = Field("test-client", description="test client ID")
    valid_seconds: int = Field(
        60 * 60, description="default expiration time of access tokens in seconds"
    )


class OidcProvider:  # pylint: disable=too-many-instance-attributes
    """A test OpenID Connect provider."""

    users: dict[str, UserInfo]
    key_set: jwk.JWKSet
    issuer: str
    op_domain: str
    user_domain: str
    client_id: str
    serial_id: int
    tasks: set[asyncio.Task]

    def __init__(self, config: OidcProviderConfig) -> None:
        """Initialize the OP."""
        issuer = config.issuer
        self.issuer = issuer
        if not issuer or "://" not in issuer or "." not in issuer:
            raise ValueError(f"Invalid issuer: {issuer!r}")
        user_domain = config.user_domain
        if not user_domain or "://" in user_domain or "." not in user_domain:
            raise ValueError(f"Invalid user domain: {user_domain!r}")
        self.op_domain = ".".join(
            issuer.split("://", 1)[-1].split("/", 1)[0].rsplit(".", 2)[-2:]
        )
        self.valid_seconds = config.valid_seconds
        self.user_domain = user_domain
        self.client_id = config.client_id
        self.generate_keys()
        self.users = {}
        self.serial_id = 1
        self.tasks = set()

    async def cancel_tasks(self):
        """Cleanup all pending tasks."""
        tasks = self.tasks
        while tasks:
            task = tasks.pop()
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def reset(self):
        """Reset the OP, clear all data."""
        await self.cancel_tasks()
        self.users.clear()
        self.serial_id = 1

    def add_user(self, token: str, user: UserInfo) -> None:
        """Add the given user to the cache."""
        self.users[token] = user
        self.serial_id += 1

    def generate_keys(self) -> None:
        """Generate a key set with a key pair for signing the tokens."""
        key = generate_jwk()  # generates EC keys
        key["kid"] = "test"
        key_set = jwk.JWKSet()
        key_set.add(key)
        self.key_set = key_set

    @property
    def key(self) -> jwk.JWK:
        """Get the single key pair from the key set."""
        key = self.key_set.get_key("test")
        if key is None:
            raise KeyError("Cannot retrieve the signing key.")
        return key

    @property
    def next_jti(self):
        """Determine the next jti value."""
        return f"test-{len(self.users) + 1}"

    def add_cleanup_task(self, token: str, valid_seconds: int) -> None:
        """Add a task to remove the token in the cache after the given time."""

        async def cleanup_task(token: str, valid_seconds: int) -> None:
            """Remove the given token in the cache after the given time."""
            await asyncio.sleep(valid_seconds)
            if token in self.users:
                del self.users[token]
            self.tasks.remove(task)

        task = asyncio.create_task(cleanup_task(token, valid_seconds))
        self.tasks.add(task)

    def create_access_token(
        self,
        name: str,
        email: str | None = None,
        sub: str | None = None,
        valid_seconds: int | None = None,
    ) -> str:
        """Create and cache an access token for a given user.

        If no subject identifier is passed, it is derived from the user name.
        """
        if not name:
            raise ValueError("The name of the user must be specified.")
        if valid_seconds is None:
            valid_seconds = self.valid_seconds
        if not valid_seconds or valid_seconds < 0:
            raise ValueError("The expiration time is invalid.")
        if email:
            if "@" not in email:
                raise ValueError("The email address of the user is invalid.")
        else:
            email = name.lower().replace(" ", ".") + f"@{self.user_domain}"
        if not sub:
            user_id = "id-of-" + name.lower().replace(" ", "-")
            sub = f"{user_id}@{self.op_domain}"
        user = UserInfo(sub=sub, email=email, name=name)
        jti = f"test-{self.serial_id}"
        claims = {
            "jti": jti,
            "sid": jti,
            "iss": self.issuer,
            "sub": sub,
            "client_id": self.client_id,
            "token_class": "access_token",
            "scope": "openid profile email",
            "aud": [self.client_id],
        }
        token = sign_and_serialize_token(
            claims, key=self.key, valid_seconds=valid_seconds
        )
        self.add_user(token, user)
        self.add_cleanup_task(token, valid_seconds)
        return token

    def get_user_info(self, token: str) -> UserInfo:
        """Return the user info associated with the given access token.

        Raises a KeyError if no user info is associated with the given token.
        This means the token is invalid in the context of this OP provider.
        """
        return self.users[token]

    def decode_and_validate_token(self, token: str) -> dict[str, Any]:
        """Decode and validate the given token."""
        return decode_and_validate_token(token, self.key)
