FROM python:3.9
WORKDIR /code
COPY ./requirements-service.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./reasoner_validator /code/reasoner_validator
COPY ./app /code/app
EXPOSE 80
CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
