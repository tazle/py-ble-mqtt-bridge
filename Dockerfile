ARG BASE_IMAGE=resin/rpi-raspbian:stretch
FROM ${BASE_IMAGE} AS build
RUN apt-get update && apt-get --no-install-recommends -y install python3 python3-pip python3-psutil gdb python-dbg git
RUN pip3 install --upgrade pip
RUN pip3 install setuptools

COPY requirements.txt /
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3", "post_to_mqtt.py"]

COPY post_to_mqtt.py /

