# MCP Chat Application

This is a simple Django-based chat application that demonstrates how to integrate with a Multi-Capability Protocol (MCP) compliant agent. The application allows users to upload documents and then chat with an AI agent that can use the content of those documents to answer questions.

## Features

-   Document upload (text and PDF).
-   Text extraction from uploaded documents.
-   A simple chat interface to interact with an AI agent.
-   An MCP-like manifest to expose uploaded documents as resources.

## Project Structure

The project is organized as follows:

```
mcp_chat/
├── docker-compose.yml
└── mcp_app/
    ├── Dockerfile
    ├── entrypoint.sh
    ├── manage.py
    ├── requirements.txt
    ├── chatapp/
    │   ├── migrations/
    │   ├── static/
    │   ├── templates/
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── models.py
    │   ├── tests.py
    │   ├── urls.py
    │   └── views.py
    └── mcp_app/
        ├── __init__.py
        ├── asgi.py
        ├── settings.py
        ├── urls.py
        └── wsgi.py
```

## How to Run

This project is designed to be run with Docker and Docker Compose.

### Prerequisites

-   Docker
-   Docker Compose

### Running the Application

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd mcp_chat
    ```

2.  **Environment Variables:**
    The application uses environment variables defined in `docker-compose.yml` to configure the Django settings. You can create a `.env` file in the root of the project to override the default values. The most important variables are:
    -   `DJANGO_SECRET_KEY`: A secret key for your Django application.
    -   `AI_AGENT_API_URL`: The URL of the AI agent you want to connect to.
    -   `AI_AGENT_API_AUTH`: The authentication token for the AI agent (e.g., `Bearer <your-token>`).

3.  **Build and run the containers:**
    ```bash
    docker-compose up --build
    ```
    This will build the Docker image for the web application and start the web and database containers.

4.  **Access the application:**
    Once the containers are running, you can access the application at `http://localhost:8000`.

### Running Management Commands

You can run Django management commands using `docker-compose exec`. For example, to create a superuser:

```bash
docker-compose exec web python manage.py createsuperuser
```

## How it Works

-   **Backend**: The backend is a Django application that serves the chat interface and provides an API for the AI agent to access documents.
-   **Frontend**: The frontend is a simple HTML/CSS/JavaScript interface that allows users to upload documents and chat with the AI agent.
-   **MCP Integration**: The application exposes a manifest at `/mcp/manifest/` that lists the available documents. The AI agent can then fetch the content of these documents using the URLs provided in the manifest.
-   **Database**: A PostgreSQL database is used to store document metadata and extracted text.
