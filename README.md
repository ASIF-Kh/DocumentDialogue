# DocuChat

A powerful document chatbot application that allows users to upload, manage, and chat with various documents (PDFs, DOCXs, TXTs) using advanced AI.

## Features

- **User Authentication**: Secure login and registration system
- **Document Management**: Upload, view, and delete documents
- **Multi-Document Upload**: Upload multiple files at once
- **AI-Powered Chat**: Interact with document content through natural language
- **Multi-Document Chat**: Create chat sessions that can query across multiple documents
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **Backend**: Python with Flask framework
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Vector Database**: ChromaDB for document embeddings
- **Natural Language Processing**:
  - OpenAI GPT models via LangChain
  - PDF, DOCX, and TXT processing
- **Frontend**:
  - Bootstrap CSS for responsive design
  - JavaScript for interactive components

## Requirements

- Python 3.10+
- OpenAI API key

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd docuchat
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

4. Initialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. Run the application:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```
   
   Alternatively:
   ```
   python main.py
   ```

## Usage

1. Register a new account or log in
2. Upload one or more documents from the dashboard
3. Wait for document processing to complete (indicated by "Processed" status)
4. Start a chat with any processed document by clicking the "Chat" button
5. Create multi-document chats by clicking "Create Multi-Document Chat" and selecting multiple documents
6. Ask questions about your documents and receive AI-generated answers

## Document Support

- **PDF**: Full text extraction with page metadata
- **DOCX**: Microsoft Word documents with text content extraction
- **TXT**: Plain text files

## Multi-Document Chat

The multi-document chat feature allows users to:
- Create chat sessions with 2+ documents
- Ask questions that require information from multiple sources
- Receive comprehensive answers that synthesize information from all selected documents
- See clear document source citations in the responses

## Architecture

The application follows a modular architecture:

- **Routes**: Organized by functionality (auth, document, chat)
- **Models**: SQLAlchemy models for data persistence
- **Templates**: Jinja2 templates for the UI
- **Utils**: Document processing and chat functionality

## Security Features

- Password hashing using Werkzeug
- Form validations with CSRF protection
- User session management
- Secure document storage with randomized filenames

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with the LangChain and OpenAI ecosystem
- Designed for seamless document interaction and information retrieval