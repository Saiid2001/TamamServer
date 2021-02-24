FROM python:3.8-slim-buster

ADD . /api
WORKDIR /api
COPY requirements.txt .
COPY . .
RUN pip install -r requirements.txt
RUN pip install gunicorn
CMD ["uwsgi", "--ini", "uwsgi.ini"]
CMD [ "gunicorn", "-w", "4", "--bind", "0.0.0.0:5000", "wsgi"]
CMD python app.py

EXPOSE 4000

ENTRYPOINT ["python", "/api/app.py"]