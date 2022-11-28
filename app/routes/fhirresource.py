import os
import duckdb
from deltalake import DeltaTable, PyDeltaTableError
from loguru import logger
from typing import Dict
from fastapi import APIRouter, Depends

from ..core.settings import get_settings
from ..common import get_delta_table, Resource, get_resource_data

router = APIRouter()


@router.get(
    path="", response_model=Dict, operation_id="get_resource", summary="Gets data for the given fhir resource")
async def get_resource(
        resource: Resource, yy__patient_id: str, system_name: str, config=Depends(get_settings)):
    """

    @param resource:
    @param yy__patient_id:
    @param system_name:
    @param config:
    @return:
    """

    logger.info(f'Resource: {resource.value}')
    if system_name not in config.system_config['systems'][system_name]:
        files = get_resource_data(
            input_dir=os.path.join(
                config.system_config['paths']['base_path'],
                config.system_config['systems'][system_name]['db_name']),
            resource='observation',
            partition_column_data=[("yy__patient_id", "=", yy__patient_id)])

        if not files:
            return {'message': "No files found"}

        duckdb_con = duckdb.connect()
        data = duckdb_con.execute(
            f'select * from read_parquet({files})').fetch_arrow_table().to_pylist()
        duckdb_con.close()
        return {'data': data[0: 100], "message": "Success"}
    else:
        return {'message': f"System - {system_name} not found"}