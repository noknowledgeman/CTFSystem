FROM python:latest
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# I dont like that I have to rebuild evvery time 
COPY . .

# I am not sure if this is necessary
RUN python ./scripts/init_db.py

CMD [ "uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]