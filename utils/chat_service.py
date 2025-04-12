import os
import logging
from openai import OpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

from utils.document_processor import get_document_chroma
from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKEN_LIMIT

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_answer(query, document_id, user_id, chat_history=None):
    """Generate an answer to a user query based on document content"""
    try:
        # Get the document's ChromaDB collection
        vector_store = get_document_chroma(document_id, user_id)
        if not vector_store:
            return {"error": "Failed to load document data"}
        
        # Create the retriever
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Initialize memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
            output_key="answer"
        )
        
        # Add chat history to memory if provided
        if chat_history:
            for message in chat_history:
                if message["is_user"]:
                    memory.chat_memory.add_user_message(message["content"])
                else:
                    memory.chat_memory.add_ai_message(message["content"])
        
        # Create the conversation chain
        llm = ChatOpenAI(
            temperature=0,
            model=OPENAI_MODEL,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            openai_api_key=OPENAI_API_KEY,
            max_tokens=MAX_TOKEN_LIMIT
        )
        
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            verbose=True
        )
        
        # Run the chain
        result = qa_chain({"question": query})
        
        return {
            "answer": result["answer"],
            "sources": [doc.metadata.get("filename", "Unknown") for doc in result.get("source_documents", [])]
        }
        
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        return {"error": f"Failed to generate answer: {str(e)}"}

def direct_openai_query(query, context):
    """Fallback method to directly query OpenAI"""
    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": "You are a helpful assistant answering questions based on the provided document context."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
            ],
            temperature=0,
            max_tokens=MAX_TOKEN_LIMIT
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        logger.error(f"Error with direct OpenAI query: {str(e)}")
        return {"error": f"Failed to generate answer: {str(e)}"}
