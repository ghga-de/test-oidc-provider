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

"""Models used by the API"""

from typing import Optional, Union

from pydantic import BaseModel, EmailStr, Field, PositiveFloat, PositiveInt

__all__ = ["LoginInfo", "UserInfo"]


class LoginInfo(BaseModel):
    """Data that is used to login as a user."""

    sub: Optional[str] = Field(None, description="subject identifier")
    email: Optional[EmailStr] = Field(None, description="e-mail address of the user")
    name: str = Field(..., description="the full name of the user")
    valid_seconds: Optional[Union[PositiveInt, PositiveFloat]] = Field(
        None, description="seconds until the login expires"
    )


class UserInfo(BaseModel):
    """Data that is returned by the UserInfo endpoint."""

    sub: str = Field(..., description="subject identifier")
    email: EmailStr = Field(..., description="e-mail address of the user")
    name: str = Field(..., description="the full name of the user")
