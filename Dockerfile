# Use a very small, lightweight version of Python 3.9
FROM python:3.9-slim

# Create and set the working directory inside the container
WORKDIR /app

# Copy the python script from your repo into the container's /app directory
COPY exam-source-app.py .

# Install Flask so the application can run
RUN pip install flask

# Set an environment variable inside the container (defaulting to 5000)
ENV PORT=5000

# Tell Docker that the container will listen on port 5000
EXPOSE 5000

# The exact command to execute when the container is started
CMD ["python", "exam-source-app.py"]
