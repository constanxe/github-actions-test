FROM python:latest
WORKDIR /usr/src/app
COPY requirements.txt ./
COPY client ./client
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app.py .
CMD [ "python", "./app.py" ]