
FROM python:2.7-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python setup.py install

#CMD [ h3cc ]
CMD gunicorn --error-logfile - --access-logfile - --bind 0.0.0.0:8000 --workers 10 hapy.dash.dashboard:app

