# Taleified AI Engine Documentation

## Project Overview

Taleified AI Engine is a Python-based backend service designed to process and generate images for a book creation platform. The application provides APIs for uploading images and processing book pages with AI-generated content.

## Project Structure

```
taleified-ai-engine/
├── app/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py        # Application configuration
│   ├── dependencies/
│   │   ├── __init__.py
│   │   ├── database.py       # Database connection handling
│   │   └── dependencies.py   # FastAPI dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic models and schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── images.py         # Image upload endpoints
│   │   └── processing.py     # Book processing endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_service.py  # Image handling logic
│   │   └── processing_service.py  # Core processing logic
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── helpers.py        # Helper functions
│   └── main.py               # FastAPI application entry point
├── views/
│   └── home/
│       └── index.html      # Basic web interface
├── requirements.txt           # Python dependencies
└── run.py                    # Application runner
```

## Core Components

### 1. API Endpoints

#### Image Processing

- `POST /images/upload`
  - Upload an image file
  - Returns: URL of the uploaded image

#### Book Processing

- `POST /process/book`

  - Start processing a book with provided details
  - Accepts: BookDetails schema
  - Returns: ProcessResponse with process_id
- `GET /process/status/{process_id}`

  - Get status of a processing job
  - Returns: Current process status and details

### 2. Data Models

#### ProcessStatus (Enum)

- PENDING: Initial state
- PROCESSING: Currently being processed
- COMPLETED: Successfully finished
- FAILED: Processing failed

#### PageData

- `id`: Page identifier (int)
- `source_url`: Source image URL
- `target_url`: Target image URL
- `prompt`: Text prompt for AI processing
- `style`: Styling information

#### BookDetails

- `user_id`: ID of the user
- `book_id`: Unique book identifier
- `pages`: List of PageData objects

### 3. Services

#### ImageService

- Validates and saves uploaded images
- Handles file storage and URL generation
- Implements file format and size validation

#### ProcessingService

- Manages book processing workflow
- Handles background tasks
- Tracks process status
- Validates input data

### 4. Validation

#### ProcessValidator

- Validates book details structure
- Checks required fields and formats
- Validates page data and image URLs
- Provides detailed error messages

### 5. Error Handling

Custom exceptions and error responses with:

- Error type
- Human-readable message
- Error code
- Additional details when applicable

## Technical Stack

- **Framework**: FastAPI
- **Language**: Python 3.x
- **Data Validation**: Pydantic
- **File Handling**: Python standard library
- **Asynchronous Processing**: FastAPI BackgroundTasks

## Setup and Running

### Step 1: Install Python

1. Visit the [Python Downloads Page](https://www.python.org/downloads/)
2. Download the latest Python version (3.8 or newer)
3. Run the installer
4. Check "Add Python to PATH" during installation
5. Click "Install Now"
6. Verify installation by opening Command Prompt (Windows) and typing:
   ```bash
   python --version
   ```

### Step 2: Download the Project

```bash
git clone https://github.com/euitsol/taleified-ai-engine.git
cd taleified-ai-engine
```

### Step 3: Set Up Virtual Environment

Create and activate a virtual environment:

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Run the Application

```bash
python run.py
```

### Step 6: Access the Application

- API documentation: http://localhost:8000/docs
- Interactive API docs: http://localhost:8000/redoc
- Home page: http://localhost:8000

## Error Codes

### Validation Errors (1000-1999)

- 1001: File size exceeds limit
- 1002: Invalid file format
- 1004: Process not found

### Book Processing Errors (2000-2999)

- 2001: At least one page is required
- 2002: Invalid source URL format
- 2003: Invalid target URL format
- 2004: Invalid prompt length
- 2005: Book ID is required
- 2006: User ID is required
- 2007: Invalid image URL
