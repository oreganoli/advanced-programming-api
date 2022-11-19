import cv2
from http import HTTPStatus
import sympy
import numpy as np
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import Response

app = FastAPI()


@app.get("/prime/{num}")
async def is_prime(num: int) -> bool:
    return sympy.isprime(num)


@app.post("/invert")
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
