FROM python:3.9

RUN pip install --upgrade pip \
  && pip install poetry

RUN mkdir /local

COPY . /local

WORKDIR /local

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

CMD /bin/bash