"""
This module contains all project related settings.
"""
import os
import toml
from functools import lru_cache
from os import path
from typing import List, Dict

import requests
from pydantic import BaseSettings, Extra, HttpUrl, SecretStr, PostgresDsn


class KeycloakModel(BaseSettings):
    """Keycloak Settings"""

    keycloak_realm: str = ""
    keycloak_auth_url: HttpUrl = "https://auth.314ecorp.tech"
    keycloak_client_id: str = ""
    keycloak_client_uuid: str = "d1a86e28-991d-4938-bcc9-dde376ae3035"
    keycloak_credential: SecretStr = ""
    keycloak_identity_provider_client_id: str = ""
    keycloak_identity_provider_client_secret: str = ""

    @property
    def keycloak_wellknown_url(self):
        """Returns keycloak well-known url"""
        return f"{self.keycloak_auth_url}/auth/realms/{self.keycloak_realm}/.well-known/openid-configuration"

    class Config(BaseSettings.Config):
        """Config Function"""

        extra: Extra = Extra.ignore


class GSuiteModel(BaseSettings):
    type: str = "service_account"
    project_id: str = "e235711"
    private_key_id: str = ""
    private_key: str = ""
    client_email: str = ""
    client_id: str = ""
    auth_uri: HttpUrl = "https://accounts.google.com/o/oauth2/auth"
    token_uri: HttpUrl = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url: HttpUrl = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url: HttpUrl = "https://www.googleapis.com/robot/v1/metadata/x509/app-314e%40e235711.iam.gserviceaccount.com"

    class Config(BaseSettings.Config):
        extra: Extra = Extra.ignore


class AppSettings(BaseSettings):
    """
    Default settings
    """

    client_code: str = os.getenv("CLIENT_CODE", "test1")
    db_schema_name: str = os.getenv("DB_SCHEMA_NAME", "test1")
    log_path: str = "/var/log" if os.getuid() == 0 else "/tmp"
    if not path.exists(log_path):
        os.makedirs(log_path)
    log_file_path: str = path.join(log_path, "muspell_etl_app.log")
    api_prefix: str = "/api/v1"
    log_level: str = "DEBUG"
    deployment: str = "integration"

    # pg_dsn: PostgresDsn = "postgresql://user:pass@localhost"

    # keycloak settings
    keycloak: KeycloakModel = KeycloakModel()
    keycloak_auth_url: HttpUrl = "https://auth.314ecorp.tech"
    keycloak_realm_path: str = "/auth/admin/realms/"
    auth_secret: str = ""
    auth_user: str = "installer"

    spark_driver_url: str = ''

    gsuite: GSuiteModel = GSuiteModel()

    # dns_domain: str = ""
    ui_repo_branch: str = "sprint"
    task_num_retry: int = 5
    oauth_scope: List = ["email", "profile", "offline_access"]
    oauth_redirect_server_port: int = 10851
    oauth_redirect_url: str = f"http://localhost:{oauth_redirect_server_port}/callback"
    oauth_response_file: str = path.join(
        path.dirname(path.realpath(__file__)), "loginHandlerResponse.html"
    )
    system_config: Dict = {}

    class Config(BaseSettings.Config):
        """Config Function"""
        extra: Extra = Extra.ignore


class IntegrationSettings(AppSettings):
    """
    Integration settings
    """

    client_code: str = os.getenv("CLIENT_CODE", "test1")
    api_prefix: str = "/api/v1"
    log_level: str = "DEBUG"
    deployment: str = "integration"

    # pg_dsn: PostgresDsn = "postgresql://user:pass@localhost"
    queue_url: str = ""

    # keycloak settings
    keycloak_auth_url: HttpUrl = os.getenv(
        "keycloak_auth_url", "https://auth.314ecorp.tech"
    )
    keycloak_realm_path: str = "/auth/admin/realms/"
    auth_secret: str = ""
    auth_user: str = "installer"
    keycloak: KeycloakModel = KeycloakModel(keycloak_auth_url=keycloak_auth_url)

    spark_driver_url: str = 'http://localhost:18080/api/v1'

    # dns_domain: str = ""
    ui_repo_branch: str = "sprint"

    class Config(BaseSettings.Config):
        """Config Function"""
        extra: Extra = Extra.ignore


class ProductionSettings(AppSettings):
    """
    Production settings
    """

    client_code: str = os.getenv("CLIENT_CODE", "demo1")
    api_prefix: str = "/api/v1"
    log_level: str = "WARN"
    deployment: str = "production"

    # pg_dsn: PostgresDsn = "postgresql://user:pass@localhost"
    queue_url: str = ""

    # keycloak settings
    keycloak_auth_url: HttpUrl = os.getenv("keycloak_auth_url", "https://auth.314ecorp.com")
    keycloak_realm_path: str = "/auth/admin/realms/"
    auth_secret: str = ""
    auth_user: str = "installer"
    keycloak: KeycloakModel = KeycloakModel(keycloak_auth_url=keycloak_auth_url)

    # dns_domain: str = ""
    ui_repo_branch: str = "production"

    class Config(BaseSettings.Config):
        """Config Function"""
        extra: Extra = Extra.ignore


@lru_cache()
def get_settings():
    """
    This function initializes the settings object based on environment DEPLOYMENT. The order in which
    the settings are applied is as follows:
    DEPLOYMENT environment creates right settings object.  This is the default base object.
    If APP_CONFIG_FILE is specified it loads all the data defined from the file
    """
    deployment: str = os.getenv("DEPLOYMENT", "integration").lower()
    settings: AppSettings = ProductionSettings() if deployment == "production" else IntegrationSettings()
    settings_file: str = os.getenv("APP_CONFIG_FILE")
    if settings_file is not None and path.exists(settings_file) and path.isfile(settings_file):
        settings = settings.parse_file(settings_file)
    settings.system_config = toml.load(os.path.join(os.path.dirname(__file__),
                                                    f"../config/{os.getenv('CUSTOMER').lower()}.toml"))
    return settings


@lru_cache()
def get_security_config():
    """
    Returns keycloak endpoints
    """
    settings: AppSettings = get_settings()
    return requests.get(settings.keycloak.keycloak_wellknown_url).json()
