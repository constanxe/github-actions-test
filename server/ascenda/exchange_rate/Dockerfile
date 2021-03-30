FROM python:latest
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./exchange_rate.py .
CMD [ "python", "./exchange_rate.py" ]