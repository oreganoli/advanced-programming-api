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


app = FastAPI()


@app.get("/prime/{num}")
async def is_prime(num: int) -> bool:
    return sympy.isprime(num)


@app.post("/picture/invert")
async def invert(file: UploadFile) -> Response:
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
    if authorization is None:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED,
                            detail="No authorization was provided.")
    try:
        claims = jwt.decode(
            authorization, "TOP SEEKRIT DONUT STEEL", algorithms=["HS256"])
    except:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail="The authorization token provided was malformed or forged and could not be decoded.")
    if claims["privileges"] is None or claims["privileges"].find("get_time") == -1:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN,
                            detail="You are not allowed to perform this operation.")
    return time.time()


@app.post("/login")
async def login(req: LoginRequest) -> str | None:
    if req.username == "EXAMPLE_USER" and req.password == "EXAMPLE_PASSWORD":
        return jwt.encode({"user": "EXAMPLE_USER", "privileges": "get_time"}, "TOP SEEKRIT DONUT STEEL")
    return None
