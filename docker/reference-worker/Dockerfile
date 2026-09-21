FROM python:3.12-alpine@sha256:9ba6d8cbebf0fb6546ae71f2a1c14f6ffd2fdab83af7e104bdfc69e795f00956
WORKDIR /app
COPY examples/worker_echo.py /app/worker.py
USER 65532:65532
ENTRYPOINT ["python", "/app/worker.py"]
