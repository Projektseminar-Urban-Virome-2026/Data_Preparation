FROM alpine:3.19

RUN apk add --no-cache sqlite

RUN apk add --no-cache python3

RUN apk add --no-cache py3-pandas

RUN apk add --no-cache py3-flask

RUN apk add --no-cache py3-flask-cors

RUN apk add --no-cache py3-joblib py3-scipy py3-statsmodels

WORKDIR /app

COPY /database/db-api.py /app/

EXPOSE 5000

CMD ["python", "db-api.py"]


