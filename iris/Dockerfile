FROM intersystemsdc/irishealth-community:latest

COPY iris.script /tmp/iris.script
RUN iris start IRIS && \
    iris session IRIS < /tmp/iris.script && \
    iris stop IRIS quietly
