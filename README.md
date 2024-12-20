# Spotify Support Chatbot 🎵🤖

🔗 **Live Demo:** [https://spotify-bot.azurewebsites.net](https://spotify-bot.azurewebsites.net)

## Authors ✨

### Course: Teknologi Sistem Terintegrasi (II3160)

- **18222019** Jonathan Wiguna

### Course: Layanan Sistem dan Teknologi Informasi (II3120)

- **18222019** Jonathan Wiguna
- **18222023** Thalita Zahra Sutejo
- **18222059** Eleanor Cordelia
- **18222065** Naomi Pricilla Agustine
- **18222093** Micky Valentino

This application serves as:

- Prototype for the final milestone of II3120 (Layanan Sistem dan Teknologi Informasi)
- Final project for II3160 (Teknologi Sistem Terintegrasi)

## Project Overview

An AI-powered chatbot built with FastAPI that provides intelligent support for Spotify-related queries. The bot uses natural language processing to understand user questions and provide relevant, contextual responses about Spotify features, troubleshooting, and general support.

## Tech Stack 💻

- **Backend**: FastAPI (Python 3.12)
- **Frontend**: HTML, CSS, JavaScript
- **Database**: Supabase

3. **Decision Tree Navigation**:
  - Structured as a hierarchical JSON
  - Each node contains:
    - Keywords for matching
    - Response templates
    - Follow-up questions
    - Child nodes for deeper context and personalization

### Decision Tree Structure
The bot's response quality heavily depends on the decision tree's comprehensiveness:
- Root nodes handle general categories (account, playback, billing, etc.)
- Branch nodes contain specific issues, potential causes, and solutions
- Leaf nodes provide detailed responses and troubleshooting steps
- Response variations based on user frustration level 

## Local Development 🛠️

### Prerequisites
- Python 3.12
- Docker
- Supabase account

### Setup and Installation

1. Clone the repository:
    - git clone https://github.com/yourusername/spotify-support-bot.git
    - cd spotify-support-bot

2. Create .env file in the root directory:
    - SUPABASE_URL=your_supabase_url
    - SUPABASE_KEY=your_supabase_key

3. Build and run with Docker Compose:
    - docker-compose up --build

## Don't forget to change the email configuration

The application will be available locally at http://localhost:8000 for testing and debugging.
