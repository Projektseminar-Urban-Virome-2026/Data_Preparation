FROM alpine:3.19

WORKDIR /work

RUN apk add --no-cache \
    python3 \
    py3-pandas \
    py3-joblib \
    py3-scipy \
    py3-statsmodels \
    py3-yaml

CMD ["python", "models/train_if_missing.py", "--config", "models/config.yaml"]
