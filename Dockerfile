ARG BASE_IMAGE=resin/rpi-raspbian:stretch
FROM ${BASE_IMAGE} AS build
RUN apt-get update && apt-get --no-install-recommends -y install python3 python3-pip python3-psutil gdb python-dbg git
RUN pip3 install --upgrade pip
RUN pip3 install setuptools

COPY requirements.txt /
RUN pip3 install -r requirements.txt


FROM ${BASE_IMAGE}

RUN apt-get update && apt-get --no-install-recommends -y install python3 && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/local/lib/python3.5/dist-packages/ /usr/local/lib/python3.5/dist-packages
COPY --from=build /src/ /src

COPY post_to_mqtt.py /

ENTRYPOINT ["python3", "post_to_mqtt.py"]
