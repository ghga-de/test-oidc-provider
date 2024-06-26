# Copyright 2021 - 2024 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
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

"""HTTP Utilities"""

from fastapi import Request

__all__ = ["get_original_url"]


def get_original_url(request: Request) -> str:
    """Get the original URL used for the request."""
    headers = request.headers
    print("Request headers:", headers)
    original_path = headers.get("x-forwarded-path") or headers.get(
        "x-envoy-original-path"
    )
    print("Original Path:", original_path)
    if original_path:
        # construct the URL from the header values
        host = (
            headers.get("x-forwarded-host")
            or headers.get("x-envoy-original-host")
            or headers.get("host")
            or request.url.netloc
        )
        scheme = (
            headers.get("x-forwarded-proto")
            or headers.get("x-envoy-original-proto")
            or request.url.scheme
        )
        original_url = f"{scheme}://{host}"
    else:
        # get the URL for this endpoint sans query params
        original_url = str(request.url.replace(query=None))
    print("Original URL:", original_url)
    return original_url
