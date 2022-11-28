import aiohttp
import asyncio
from typing import Dict, List
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..core.settings import get_settings
from ..common import get_data, get_paginated_data


router = APIRouter()


class RequestModel(BaseModel):
    method: str
    url: str


class Entry(BaseModel):
    request: RequestModel


class Bundle(BaseModel):
    resourceType: str
    id:  str
    type:  str
    entry: List[Entry]


@router.post("/bundle")
async def get_data(request: Request, bundle: Bundle):
    data_list = []
    async with aiohttp.ClientSession() as session:
        for entry in bundle.entry:
            url = f"{str(request.base_url)[:-1]}{entry.request.url}"
            async with session.get(url) as resp:
                data = await resp.json()
                data_list.append(data)
    return data_list



