from fastapi import Request
from http import HTTPStatus
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from .utils import Params, get_access_token
from ..config import logger, ConfigServer


class AccessTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, req: Request, call_next) -> Response:
        logger.info(f"Request Path: {req.url.path}")

        check_master: Response | None = self.__check_master(req=req)
        if check_master is not None:
            return check_master

        check_access: Response | None = self.__check_access(req=req)
        if check_access is not None:
            return check_access

        return await call_next(req)

    def __check_master(self, req: Request) -> Response | None:
        if require_master_token(req):
            access_token: str = req.headers.get("MASTER-TOKEN")
            required_token: str = ConfigServer.MASTER_TOKEN

            if access_token != required_token or access_token is None:
                return JSONResponse(
                    content={"detail": "Unauthorized Master Token"},
                    status_code=HTTPStatus.UNAUTHORIZED,
                )

        return None

    def __check_access(self, req: Request) -> Response | None:
        if require_access_token(req):
            client_id: str | None = Params(req).get_param("client_id")
            access_token: str = req.headers.get("ACCESS-TOKEN")
            required_token: str = get_access_token(client_id)

            if required_token is None:
                return JSONResponse(
                    content={"detail": "Invalid Client ID"},
                    status_code=HTTPStatus.UNAUTHORIZED,
                )

            if access_token is None or required_token != access_token:
                return JSONResponse(
                    content={"detail": "Unauthorized Access Token"},
                    status_code=HTTPStatus.UNAUTHORIZED,
                )

        return None


def require_master_token(req: Request) -> bool:
    for path in ConfigServer.MASTER_PATHS:
        if req.url.path.startswith(path):
            return True
    return False


def require_access_token(req: Request) -> bool:
    for path in ConfigServer.ACCESS_TOKEN_PATHS:
        if req.url.path.startswith(path):
            return True
    return False
