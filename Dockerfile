FROM python:3.10-slim

USER root
RUN apt-get update && apt-get install python3-distutils-extra python3-pip -y
RUN apt-get install -y chromium
RUN python3 -m pip install selenium cs-rankings webdriver-manager
RUN apt-get install git -y
