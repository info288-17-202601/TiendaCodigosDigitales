# Python version - Uses slim for storage efficency
FROM python:3.10-slim

# Work directory inside container - Following commands run here
WORKDIR /app

# Copy dependencies from requirements.txt
COPY requirements.txt .

# Installs libraries using dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copies code from backend
COPY . .

# Expose port where flask will run
EXPOSE 5050

# Executes api
CMD ["python", "app.py"]