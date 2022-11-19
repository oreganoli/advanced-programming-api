import sympy
from fastapi import FastAPI

app = FastAPI()


@app.get("/prime/{num}")
async def is_prime(num: int) -> bool:
    return sympy.isprime(num)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
