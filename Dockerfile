#Dockerfile, Image, Container
FROM python:3.9

COPY requirements.txt .

RUN pip install -r requirements.txt

ADD dining.py .

ADD foods.py .

CMD ["python", "./dining.py"]