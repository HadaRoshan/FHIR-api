
from typing import Dict
from fastapi import APIRouter, Depends


from ..core.settings import get_settings
from ..common import get_data, get_paginated_data
router = APIRouter()

RESOURCE_TYPE = 'MedicationDispense'


@router.get(
    path=f"/{RESOURCE_TYPE}", response_model=Dict, operation_id="get_medicationdispense",
    summary="Gets medicationdispense data")
async def get_medicationdispense(system_name: str, patient: str = None, config=Depends(get_settings), page_num: int = 1,
                                 page_size: int = 10):
    data = get_data(RESOURCE_TYPE, system_name, patient, config)

    return get_paginated_data(data, page_num, page_size)