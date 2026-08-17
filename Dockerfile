FROM python:3.9-slim
WORKDIR /app
COPY exam-source-app.py .
RUN pip install flask
ENV PORT=5000
EXPOSE 5000
CMD ["python", "exam-source-app.py"]
