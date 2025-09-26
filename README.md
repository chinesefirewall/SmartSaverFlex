# SmartSaver Flex Vault Demo

A hackathon project demonstrating an investment platform with an AI advisor using OpenAI's API.

## Project Structure

```
smartsaver_demo/
│
├── truth.json          # your rules/config
├── calculator.py       # math logic
├── app.py              # FastAPI backend
├── advisor.py          # chatbot with OpenAI
├── demo.py             # Streamlit front-end
└── requirements.txt    # dependencies
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up OpenAI API Key

The application requires an OpenAI API key to function. Set it as an environment variable:

```bash
# For Linux/Mac
export OPENAI_API_KEY=your_api_key_here

# For Windows
set OPENAI_API_KEY=your_api_key_here
```

### 3. Run the Application

Start the FastAPI backend:
```bash
uvicorn app:app --reload
```

In a separate terminal, start the Streamlit frontend:
```bash
streamlit run demo.py
```

## Troubleshooting

### OpenAI API Issues

If you see the error message "I'm having trouble connecting to my knowledge base", it could be due to:

1. **Missing or invalid API key**: Make sure your OPENAI_API_KEY environment variable is set correctly
2. **Rate limiting**: You might have exceeded your OpenAI API quota
3. **Network issues**: Check your internet connection
4. **OpenAI service issues**: The OpenAI API might be experiencing downtime

### Enabling Debug Mode

To get more detailed error messages, enable debug mode by setting the DEBUG environment variable:

```bash
# For Linux/Mac
export DEBUG=true

# For Windows
set DEBUG=true
```

With debug mode enabled, the application will show the actual error message from the OpenAI API instead of the generic fallback message.

### Common Errors

1. **Authentication Error**: Your API key is invalid or has expired
2. **Rate Limit Error**: You've exceeded your quota or rate limits
3. **API Error**: There's an issue with the OpenAI service
4. **Connection Error**: Network connectivity issues

## API Compatibility

The application is designed to work with both older (<1.0.0) and newer (>=1.0.0) versions of the OpenAI Python client library. 

### OpenAI Client Version Notes

If you encounter the error `ModuleNotFoundError: No module named 'openai.error'`, this is because you're using a newer version of the OpenAI client (v1.0.0+) where the error module structure has changed. The application has been updated to handle this automatically.

For reference:
- In OpenAI client v0.x.x, error classes are in `openai.error`
- In OpenAI client v1.x.x, error classes are imported directly from `openai`

You don't need to make any changes to your code - the application will detect which version you're using and adapt accordingly.
