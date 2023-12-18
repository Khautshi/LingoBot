FROM python:3.11
WORKDIR D:/LingoBot
COPY requirements.txt D:/LingoBot/
RUN pip install -r requirements.txt
COPY . D:/LingoBot
CMD python main.py