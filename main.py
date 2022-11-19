import sympy
from fastapi import FastAPI

app = FastAPI()


@app.get("/prime/{num}")
async def is_prime(num: int) -> bool:
    return sympy.isprime(num)