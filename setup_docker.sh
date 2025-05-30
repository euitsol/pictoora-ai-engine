#!/bin/bash

# Update system
sudo dnf update -y

# Install required packages
sudo dnf install -y dnf-utils git

# Add Docker repository
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Install Docker
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Create directory for the project
mkdir -p /var/www/pictoora
cd /var/www/pictoora

# Clone the project
git clone https://github.com/YOUR_USERNAME/pictoora-ai-engine.git .

# Create necessary directories with proper permissions
mkdir -p storage logs
chmod -R 755 storage logs

# Create .env file (you'll need to fill this with your actual values)
cat > .env << EOL
# Add your environment variables here
OPENAI_API_KEY=your_openai_api_key
# Add other required environment variables
EOL

# Start the application with Docker Compose
sudo docker compose up -d --build

# Show the running containers
sudo docker ps

# Print the logs
echo "To view logs, run: sudo docker compose logs -f" 