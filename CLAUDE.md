# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Instagram scraping tool with a Tkinter GUI that extracts public profile information, posts, followers, and engagement data (comments, likes) from Instagram accounts. The tool uses Instagram's web API endpoints and includes advanced features like incremental data updates and detailed engagement analysis.

**SECURITY WARNING**: This tool scrapes Instagram data using login credentials and should only be used for legitimate, educational, and research purposes in compliance with Instagram's Terms of Service and applicable laws.

## Key Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run the main scraper GUI
python instagram-scrapper.py
```

### Data Analysis Scripts
```bash
# Generate markdown tables for specific profiles
python generar_tabla_cliniqmedellin.py    # For @cliniqmedellin
python generar_tabla_martaveno.py         # For @martaveno  
python generate_danielduque_table.py      # For @danielduquevel

# General table generation
python generar_tabla_completa.py
python generate_markdown_table.py

# Data analysis
python analyze_likes.py
python diagnose_data.py
```

## Architecture Overview

### Core Components

1. **InstagramAPI Class** (`instagram-scrapper.py:153-461`): Handles all Instagram web API interactions
   - Session management with proper headers and CSRF tokens
   - Login authentication using Instagram's login endpoints
   - Profile info extraction via web_profile_info API
   - Posts retrieval with pagination support
   - Detailed comments extraction with replies
   - Likes extraction with user information

2. **IncrementalDataManager Class** (`instagram-scrapper.py:10-151`): Manages smart data updates
   - Loads existing scraped data from JSON files
   - Identifies new vs existing posts, comments, and likes
   - Merges new data with existing data intelligently
   - Preserves data integrity across multiple scraping sessions

3. **InstagramScraperApp Class** (`instagram-scrapper.py:462-787`): Tkinter GUI application
   - Purple/black themed interface with real-time logging
   - Login form with credential management
   - Scraping options (comments, likes, replies, incremental mode)
   - Multi-threaded operation to prevent UI freezing

### Data Flow

1. **Authentication**: User provides Instagram credentials → API establishes session
2. **Profile Analysis**: Target username → Profile info extraction → Privacy check
3. **Post Retrieval**: Paginated post fetching with configurable limits
4. **Engagement Extraction**: Comments, replies, and likes for each post (optional)
5. **Data Merging**: Intelligent combination with existing data (incremental mode)
6. **Export**: JSON format with comprehensive metadata

### Configuration System

The `config.py` file contains all configurable parameters:
- Request delays and timeouts for rate limiting
- UI theme colors and dimensions  
- Default scraping limits (posts, comments, likes)
- Feature toggles (incremental mode, detailed extraction)
- Output formatting options

## Key Features

### Incremental Mode (`INCREMENTAL_MODE_GUIDE.md`)
- Avoids re-scraping existing content
- Only processes new posts, comments, and likes
- Significantly reduces scraping time on subsequent runs
- Maintains complete historical data

### Detailed Engagement Analysis
- Extracts comment text, authors, timestamps, and like counts
- Retrieves comment replies with full threading
- Collects like lists with user profiles and verification status
- Provides comprehensive engagement statistics

### Data Export Formats
- Primary: JSON with structured profile and posts data
- Secondary: Markdown tables for specific profiles
- Includes metadata about scraping sessions and incremental updates

## Important Considerations

### Rate Limiting
- Built-in delays between requests (`REQUEST_DELAY = 3-5 seconds`)
- Respect Instagram's API limits to avoid blocks
- Use conservative limits for comments/likes per post

### Privacy and Ethics
- Only works with public Instagram profiles
- Requires valid Instagram login credentials
- Must comply with Instagram's Terms of Service
- Intended for educational and research purposes only

### Data Integrity
- Incremental mode preserves existing data
- Automatic backup of previous data before updates
- Comprehensive error handling and logging
- JSON validation and recovery mechanisms

## Development Notes

### Dependencies
- `requests`: HTTP client for Instagram API calls
- `tkinter`: GUI framework (built-in with Python)
- `beautifulsoup4`: HTML parsing (if needed)
- `Pillow`: Image processing support

### File Structure
- `instagram-scrapper.py`: Main application file
- `config.py`: Configuration settings
- `*_table_*.py`: Data analysis and table generation scripts
- `*.json`: Scraped data files (gitignored)
- `*.md`: Generated markdown tables and documentation

### Error Handling
- Network timeouts and connection errors
- Instagram API rate limiting and blocks
- Invalid user credentials or target profiles
- JSON parsing and file I/O errors