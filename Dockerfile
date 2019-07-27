FROM python:3.6
COPY . /app
WORKDIR /app
ENV USER=root
ENV ENV=local
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ./uwsgi-start.sh
