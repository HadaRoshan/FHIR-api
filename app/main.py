"""
Main module which initializes FastAPI and required middleware
"""
import os
from typing import List, Dict
from loguru import logger
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import ORJSONResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.routing import solve_dependencies, run_endpoint_function
from fastapi.encoders import jsonable_encoder
from starlette.middleware.cors import CORSMiddleware
from starlette_prometheus import PrometheusMiddleware, metrics
from starlette.responses import FileResponse


from .core.settings import get_settings, AppSettings
from .core.log import setup_logging
from .middleware.servertiming import ServerTimingMiddleware


from .routes import (
    fhirresource, observation, account, allergyintolerance, careplan, careteam, chargeitem, claim, claimresponse,
    condition, coverage, diagnosticreport, documentreference, encounter, familymemberhistory, immunization,
    medicationadministration, medicationrequest, medicationstatement, procedure, clinicalimpression, detectedissue,
    media, specimen, bodystructure, imagingstudy, QuestionnaireResponse, molecularsequence, medicationdispense,
    immunizationevaluation, immunizationrecommendation, goal, servicerequest, nutritionorder, visionprescription,
    riskassessment, requestgroup, communication, communicationrequest, devicerequest, deviceusestatement,
    guidanceresponse, supplydelivery, bundle
)

config: AppSettings = get_settings()
api_prefix: str = config.api_prefix

setup_logging(log_file_path=config.log_file_path)
origins: List = [
    "http://localhost:8000", "http://localhost:2000", config.keycloak.keycloak_auth_url
]

ui_init_oauth: Dict = {"realm": config.keycloak.keycloak_realm, "clientId": config.keycloak.keycloak_client_id}

app = FastAPI(
    title=f"FHIR Server",
    default_response_class=ORJSONResponse,
    docs_url=None,
    redoc_url=None,
    openapi_url=f"{api_prefix}/openapi.json",
    swagger_ui_init_oauth=ui_init_oauth,

)

app.mount(
    f"{api_prefix}/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../static")),
    name="static",
)

# Add all middlewares. The order of middleware is very important
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(
    ServerTimingMiddleware,
    calls_to_track={
        "dependencies": (solve_dependencies,),
        "api_code": (run_endpoint_function,),
        "json_encoding": (jsonable_encoder,),
        "serialization": (
            JSONResponse.render,
            ORJSONResponse.render,
        ),
    },
)
app.add_route("/metrics/", metrics)


@app.get("/", include_in_schema=False)
async def read_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "../static/index.html"))


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Returns custom swagger UI"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url=f"{api_prefix}/static/swagger-ui-bundle.js",
        swagger_css_url=f"{api_prefix}/static/swagger-ui.css",
        swagger_favicon_url="https://314e.com/wp-content/uploads/2019/10/cropped-314e_logo_2016-300x300-150x150.png",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    """Returns Swagger UI oauth2 redirect HTMLComponent"""
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Return Redoc HTML"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url=f"{api_prefix}/static/redoc.standalone.js",
        redoc_favicon_url="https://314e.com/wp-content/uploads/2019/10/cropped-314e_logo_2016-300x300-150x150.png",
        with_google_fonts=False,
    )


@app.on_event("startup")
async def startup():
    """Server startup function, run whatever is required to start with server startup"""
    logger.info("Setting up application resources")
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown():
    """Server shutdown function, terminates all connections to resources"""
    logger.info("Cleaning up application resources")


app.include_router(fhirresource.router, prefix=f"{api_prefix}/fhirresource", tags=["FHIR Resource"])
app.include_router(observation.router, tags=["FHIR Resource"])
app.include_router(account.router, tags=["FHIR Resource"])
app.include_router(allergyintolerance.router, tags=["FHIR Resource"])
app.include_router(careplan.router, tags=["FHIR Resource"])
app.include_router(careteam.router, tags=["FHIR Resource"])
app.include_router(chargeitem.router, tags=["FHIR Resource"])
app.include_router(claim.router, tags=["FHIR Resource"])
app.include_router(claimresponse.router, tags=["FHIR Resource"])
app.include_router(condition.router, tags=["FHIR Resource"])
app.include_router(coverage.router, tags=["FHIR Resource"])
app.include_router(diagnosticreport.router, tags=["FHIR Resource"])
app.include_router(documentreference.router, tags=["FHIR Resource"])
app.include_router(encounter.router, tags=["FHIR Resource"])
app.include_router(familymemberhistory.router, tags=["FHIR Resource"])
app.include_router(immunization.router, tags=["FHIR Resource"])
app.include_router(medicationadministration.router, tags=["FHIR Resource"])
app.include_router(medicationrequest.router, tags=["FHIR Resource"])
app.include_router(medicationstatement.router, tags=["FHIR Resource"])
app.include_router(procedure.router, tags=["FHIR Resource"])
app.include_router(clinicalimpression.router, tags=["FHIR Resource"])
app.include_router(detectedissue.router, tags=["FHIR Resource"])
app.include_router(media.router, tags=["FHIR Resource"])
app.include_router(specimen.router, tags=["FHIR Resource"])
app.include_router(bodystructure.router, tags=["FHIR Resource"])
app.include_router(imagingstudy.router, tags=["FHIR Resource"])
app.include_router(QuestionnaireResponse.router, tags=["FHIR Resource"])
app.include_router(molecularsequence.router, tags=["FHIR Resource"])
app.include_router(medicationdispense.router, tags=["FHIR Resource"])
app.include_router(immunizationevaluation.router, tags=["FHIR Resource"])
app.include_router(immunizationrecommendation.router, tags=["FHIR Resource"])
app.include_router(goal.router, tags=["FHIR Resource"])
app.include_router(servicerequest.router, tags=["FHIR Resource"])
app.include_router(nutritionorder.router, tags=["FHIR Resource"])
app.include_router(visionprescription.router, tags=["FHIR Resource"])
app.include_router(riskassessment.router, tags=["FHIR Resource"])
app.include_router(requestgroup.router, tags=["FHIR Resource"])
app.include_router(communication.router, tags=["FHIR Resource"])
app.include_router(communicationrequest.router, tags=["FHIR Resource"])
app.include_router(devicerequest.router, tags=["FHIR Resource"])
app.include_router(deviceusestatement.router, tags=["FHIR Resource"])
app.include_router(guidanceresponse.router, tags=["FHIR Resource"])
app.include_router(supplydelivery.router, tags=["FHIR Resource"])
app.include_router(bundle.router, tags=["FHIR Resource"])
