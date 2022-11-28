import os
import duckdb
from enum import Enum
from loguru import logger
from typing import List, Tuple
from functools import lru_cache
from deltalake import DeltaTable, PyDeltaTableError

import re

@lru_cache
def get_delta_table(input_dir: str):
    """

    :param input_dir:
    :return:
    """
    return DeltaTable(input_dir)


def get_resource_data(
        input_dir, resource, partition_column_data: List[Tuple] = None):
    """

    :param input_dir:
    :param resource:
    :param partition_column_data: should follow delta-rs partition filter format,
    ex: ("x", "=", "a") ("x", "!=", "a") ("y", "in", ["a", "b", "c"]) ("z", "not in", ["a","b"])
    https://delta-io.github.io/delta-rs/python/api_reference.html
    :return:
    """
    try:
        delta_table = get_delta_table(os.path.join(input_dir, resource.lower()))
    except PyDeltaTableError as e:
        logger.warning(f'Table not found: {e}')
        return
    if partition_column_data:
        return delta_table.to_pyarrow_table(partitions=partition_column_data)
    return delta_table.to_pyarrow_table()


def execute_query(query, params):
    """

    @param query:
    @param sql_str:
    @param params:
    @return:
    """
    con = duckdb.connect()
    data = con.execute(query, params).fetch_arrow_table().to_pylist()
    con.close()
    return data


class Resource(Enum):
    """

    """
    observation = "observation"
    allergy = "allergy"
    diagnosticreport = "diagnosticreport"
    documentreference = 'documentreference'
    encounter = "encounter"

    all = "all"

    @classmethod
    def get_all_resources(cls):
        """

        :return:
        """
        return [resource for resource in cls if resource.value != cls.all.value]


def get_token_parameters(token_str: str):
    """
    :param token_str:
    :return:
    """
    if not token_str:
        return None, None
    if '|' in token_str:
        return token_str.split('|')
    else:
        return None, token_str


def get_reference_parameters(ref_str: str):
    """

    :param ref_str:
    :return:
    """
    if not ref_str:
        return None, None, None
    if 'http' in ref_str:
        return None, None, ref_str
    elif '/' in ref_str:
        return *ref_str.split('/'), None
    else:
        return None, ref_str, None


def get_quantity_parameters(quan_str: str):
    """

    :param quan_str:
    :return:
    """
    if not quan_str:
        return None, None, None
    else:
        return re.split('=||', quan_str)


def get_composite_parameters(comp_str: str):
    """
    :param comp_str:
    :return:
    """
    res = comp_str.split('|')
    return res[1], res[2]


def get_data(resource_type, system_name, patient, config):
    """

    :param resource_type:
    :param system_name:
    :param patient:
    :param config:
    :return:
    """

    resource_type=resource_type.lower()
    patient_type, patient_id, patient_url=get_reference_parameters(patient)
    if system_name not in config.system_config['systems'][system_name]:
        data=get_resource_data(
            input_dir=os.path.join(
                config.system_config['paths']['base_path'],
                config.system_config['systems'][system_name]['db_name']),
            resource=resource_type,
            partition_column_data=[("yy__patient_id", "=", patient_id)])

        if not data:
            return {'data': [], 'message': 'No files found'}

        return {'data': data.to_pylist()}


def get_paginated_data(data, page_num, page_size):
    data_length = len(data["data"])
    start = (page_num - 1) * page_size
    end = start + page_size
    response = {
        "data": data["data"][start:end],
        "total": data_length,
        "count": len(data["data"][start:end]),
        "pagination": {}
    }

    if end >= data_length:
        response["pagination"]["next"] = None

        if page_num > 1:
            response["pagination"][
                "previous"] = f"page_num={page_num - 1} & page_size={page_size}"
        else:
            response["pagination"]["previous"] = None
    else:
        if page_num > 1:
            response["pagination"][
                "previous"] = f"page_num={page_num - 1} & page_size={page_size}"
        else:
            response["pagination"]["previous"] = None

        response["pagination"]["next"] = f"page_num={page_num + 1} & page_size={page_size}"

    return response
