FROM python:latest
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./file_handling.py .
COPY ./csv_adapter.py .
CMD [ "python", "./file_handling.py" ]