FROM python:3.15.0b2-alpine3.24
WORKDIR /usr/local/app

# Install the application dependencies
COPY producer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy in the source code
COPY producer/ .

# Setup an app user so the container doesn't run as the root user
RUN adduser -D app

# Setup cron job to run manager.py every 2 minutes
# Redirect output to PID 1 stdout/stderr so docker logs can capture it
RUN echo "*/5 * * * * cd /usr/local/app && python -u manager.py >> /proc/1/fd/1 2>> /proc/1/fd/2" | crontab -

CMD ["crond", "-f"]