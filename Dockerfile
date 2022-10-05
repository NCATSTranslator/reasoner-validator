FROM python:3.9
WORKDIR /code
COPY ./requirements-service.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./reasoner_validator /code/reasoner_validator
COPY api /code/api
EXPOSE 80
CMD ["uvicorn", "api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
