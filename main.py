import os
import cv2
import jwt
import sympy
import numpy as np
import time
from http import HTTPStatus
from fastapi import FastAPI, Header, UploadFile, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
SECRET = os.environ.get("SECRET")

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
async def get_time(authorization: str | None = Header(default=None)):
    """
    Get the current time as an UTC Unix timestamp.
    Requires an authorization token to be provided in the Authorization header with the prefix "Bearer ".
    For details, see the documentation for POST /login.
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED,
                            detail="No authorization was provided or it was not a Bearer token.")
    authorization = authorization[7:]
    try:
        claims = jwt.decode(
            authorization, SECRET, algorithms=["HS256"])
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
    Log in as a user. Takes a JSON document containing the fields "username" and "password". Returns a signed JWT token that can be provided to access certain functionality - see the documentation for GET /time.
    """
    if req.username == USERNAME and req.password == PASSWORD:
        return jwt.encode({"user": req.username, "privileges": "get_time"}, SECRET)
    return None
