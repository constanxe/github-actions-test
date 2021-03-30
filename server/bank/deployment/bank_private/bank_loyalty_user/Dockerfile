FROM python:latest
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./bank_loyalty_user.py .
CMD [ "python", "./bank_loyalty_user.py" ]