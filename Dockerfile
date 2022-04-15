FROM python:3.9

COPY requirements.txt /
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "post_to_mqtt.py"]
COPY post_to_mqtt.py /
