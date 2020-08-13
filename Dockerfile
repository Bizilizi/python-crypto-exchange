FROM python:3

ADD requirements.txt /app/
RUN pip3 install -r /app/requirements.txt
ADD . /app
WORKDIR ./app

CMD ["python", "main.py"]