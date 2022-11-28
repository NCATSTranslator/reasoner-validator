FROM python:3.8

WORKDIR /code

# See the .dockerignore file to change which files are not included
COPY . .

RUN pip install .

EXPOSE 80
CMD ["uvicorn", "api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
