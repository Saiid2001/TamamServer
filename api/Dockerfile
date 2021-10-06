FROM python:3.8-slim-buster

RUN pip install pipenv

ADD . /api
WORKDIR /api

RUN pipenv install --skip-lock

COPY requirements.txt .
COPY . .

RUN pip install -r requirements.txt
RUN pip install gunicorn[gevent]

EXPOSE 5000

#CMD gunicorn --worker-class gevent --workers 8 --bind 0.0.0.0:8000 wsgi:app --max-requests 10000 --timeout 5 --keep-alive 5 --log-level info


CMD ["uwsgi", "--ini", "uwsgi.ini"]
CMD [ "gunicorn", "-w", "4", "--bind", "0.0.0.0:5000", "wsgi"]
CMD python app.py



ENTRYPOINT ["python", "/api/app.py"]