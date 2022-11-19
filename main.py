import os
import cv2
import jwt
import sympy
import numpy as np
import time
from http import HTTPStatus
from fastapi import FastAPI, Header, UploadFile, HTTPException
from fastapi.responses import Response, RedirectResponse
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
SECRET = os.environ.get("SECRET")
if USERNAME is None or PASSWORD is None or SECRET is None:
    raise Exception(
        "The USERNAME, PASSWORD and SECRET environment variables must be set.")

app = FastAPI()


@app.get("/prime/{num}")
async def is_prime(num: int) -> bool:
    """
    Given an integer, check whether it is a prime number.
    Takes an integer as a query parameter and returns a JSON bool.
    """
    if num > 9223372036854775803:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="Only numbers up to 9223372036854775803 are supported.")
    return sympy.isprime(num)


@app.post("/picture/invert")
async def invert(file: UploadFile) -> Response:
    """
    Invert an image.
    Takes a "file" field in a multipart form and returns an output image file.
    Only JPEG images of a size up to 12 megapixels are allowed.
    """
    if file.content_type != "image/jpeg":
        raise HTTPException(status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                            detail="Only JPEG images are supported.")
    image_data = np.fromfile(file.file)
    image = cv2.imdecode(image_data, cv2.IMREAD_UNCHANGED)
    if image.data == None:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="The image provided could not be decoded.")
    shape = image.data.shape
    size = 0
    if len(shape) < 2:
        size = shape[0]
    else:
        size = shape[0] * shape[1]
    if size > 12_000_000:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="The maximum supported image size is 12 Mpx.")
    # Inversion
    image.data = np.bitwise_not(image.data)
    success, output = cv2.imencode(".jpg", image)
    if not success:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail="The output image could not be successfully encoded.")
    return Response(content=output.tobytes(), media_type="image/jpeg")


@app.get("/time")
async def get_time(x_token: str | None = Header(default=None)):
    """
    Get the current time as an UTC Unix timestamp.
    Requires an authorization token to be provided in the X-Token header.
    For details, see the documentation for POST /login.
    """
    if x_token is None:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED,
                            detail="No authorization was provided.")
    try:
        claims = jwt.decode(
            x_token, SECRET, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail="The authorization token provided was malformed or forged and could not be decoded.")
    if claims["privileges"] is None or claims["privileges"].find("get_time") == -1:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN,
                            detail="You are not allowed to perform this operation.")
    return time.time()


@app.post("/login")
async def login(req: LoginRequest) -> str | None:
    """
    Log in as a user. Takes a JSON document containing the fields "username" and "password". On success, returns a signed JWT token that can be provided to access certain functionality - see the documentation for GET /time. Returns null on failure.
    """
    if req.username == USERNAME and req.password == PASSWORD:
        return jwt.encode({"user": req.username, "privileges": "get_time"}, SECRET)
    return None


@app.get("/")
async def index() -> RedirectResponse:
    return RedirectResponse("/docs")
