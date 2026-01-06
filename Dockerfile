# Use a slim Python image for smaller size
# 3.12 is selected for best compatibility with scientific libraries
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies if required (e.g. for some plotting libs)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Install python dependencies directly
# We list them here explicitly to avoid needing requirements.txt maintenance for this simple app
RUN pip install --no-cache-dir \
    streamlit \
    google-genai \
    sectionproperties \
    matplotlib \
    numpy \
    python-dotenv

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the application
ENTRYPOINT ["streamlit", "run", "main_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
