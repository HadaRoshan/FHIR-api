import jinja2
import os
from os import path
from loguru import logger
from functools import lru_cache
from jinjasql import JinjaSql

SQL_DIR = f'{os.path.dirname(__file__)}/../sql'


class SQLParser:
    def __init__(
            self, directory: str = SQL_DIR):
        """
        :param directory:
        """
        self.directory = path.join(directory)
        loader: jinja2.FileSystemLoader = jinja2.FileSystemLoader(self.directory)
        self.jsql = JinjaSql(param_style='qmark', env=jinja2.Environment(
            loader=loader, trim_blocks=True))

    def get_query(self, resource_type, params):
        """

        @param resource_type:
        @param params:
        @return:
        """
        template = self.jsql.env.get_template(f'{resource_type}.sql')
        return self.jsql.prepare_query(template, params)


@lru_cache
def get_sql_parser():
    return SQLParser()


if __name__ == "__main__":
    sql_parser = SQLParser(SQL_DIR)
    data = sql_parser.get_query('observation', {'files': ["abc"], 'patient': 'abc', 'id': 'abc'})
    print(data)
