FROM python:3.11-slim

WORKDIR /app

# Copy requirements from the project root and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot's source code
COPY bot/bot.py .

# Command to run the bot
CMD ["python", "bot.py"]
