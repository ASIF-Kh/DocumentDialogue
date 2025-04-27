import os
import logging
from openai import OpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.retrievers import EnsembleRetriever

from utils.document_processor import get_document_chroma,get_bm25_retriever
from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKEN_LIMIT

logger = logging.getLogger(__name__)

# Initialize OpenAI client
# openai_client = OpenAI(api_key=OPENAI_API_KEY)
openai_client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)

# def generate_answer(query, document_id,document_path,document_type, user_id, chat_history=None):
#     """Generate an answer to a user query based on document content"""
#     try:
#         # Get the document's ChromaDB collection
#         vector_store = get_document_chroma(document_id, user_id)
        

#         if not vector_store:
#             return {"error": "Failed to load document data"}
        
#         # Create the retriever
#         retriever = vector_store.as_retriever(
#             search_type="similarity",
#             search_kwargs={"k": 5}
#         )
#         bm25_retriever = get_bm25_retriever(document_path,document_type)
        
#         ensemble_retriever = EnsembleRetriever(retrievers=[retriever, bm25_retriever], weights=[0.5, 0.5])
        
#         # Initialize memory
#         memory = ConversationBufferMemory(
#             memory_key="chat_history",
#             return_messages=True,
#             input_key="question",
#             output_key="answer"
#         )
        
#         # Add chat history to memory if provided
#         if chat_history:
#             for message in chat_history:
#                 if message["is_user"]:
#                     memory.chat_memory.add_user_message(message["content"])
#                 else:
#                     memory.chat_memory.add_ai_message(message["content"])
        
#         # Create the conversation chain
#         # llm = ChatOpenAI(
#         #     temperature=0,
#         #     model=OPENAI_MODEL,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
#         #     openai_api_key=OPENAI_API_KEY,
#         #     max_tokens=MAX_TOKEN_LIMIT
#         # )

#         # If using Ollama, uncomment the following line
#         llm = ChatOllama(model="llama3.2:latest", temperature=0, max_tokens=MAX_TOKEN_LIMIT)

        
#         qa_chain = ConversationalRetrievalChain.from_llm(
#             llm=llm,
#             retriever=ensemble_retriever,
#             memory=memory,
#             return_source_documents=True,
#             verbose=True
#         )
        
#         # Run the chain
#         result = qa_chain({"question": query})
        
#         return {
#             "answer": result["answer"],
#             "sources": [doc.metadata.get("filename", "Unknown") for doc in result.get("source_documents", [])]
#         }
        
#     except Exception as e:
#         logger.error(f"Error generating answer: {str(e)}")
#         return {"error": f"Failed to generate answer: {str(e)}"}

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

def generate_group_answer(query, document_ids,user_id, chat_history=None):
    """Generate an answer to a user query based on multiple documents"""
    try:
        all_contexts = []
        sources = []
        
        # Retrieve context from each document
        for doc_id in document_ids:
            vector_store = get_document_chroma(doc_id, user_id)
            if not vector_store:
                continue
                
            # Create the retriever for this document
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}  # Reduced to 3 per document to prevent overloading
            )
            
            # Get relevant documents
            relevant_docs = retriever.get_relevant_documents(query)
            
            if relevant_docs:
                # Extract text and source information
                for doc in relevant_docs:
                    all_contexts.append(doc.page_content)
                    source = doc.metadata.get("filename", "Unknown")
                    if source not in sources:
                        sources.append(source)
        
        if not all_contexts:
            return {"error": "No relevant information found in the documents"}
        
        # Concatenate all contexts (with limit to avoid token overloading)
        combined_context = "\n\n".join(all_contexts)
        if len(combined_context) > 12000:  # Rough character estimate to stay within token limits
            combined_context = combined_context[:12000] + "..."
        
        # Process conversation history
        history_text = ""
        if chat_history:
            history_pairs = []
            for i in range(0, len(chat_history), 2):
                if i+1 < len(chat_history):
                    user_msg = chat_history[i]["content"]
                    assistant_msg = chat_history[i+1]["content"]
                    history_pairs.append(f"User: {user_msg}\nAssistant: {assistant_msg}")
            
            if history_pairs:
                history_text = "Previous conversation:\n" + "\n\n".join(history_pairs[-3:])  # Last 3 exchanges only
        
        # Create system prompt that instructs the model to use multiple document sources
        system_prompt = """You are a helpful assistant that answers questions based on multiple documents.
Find the most relevant information from the provided context and synthesize a comprehensive answer.
If there are contradictions between documents, acknowledge them and provide the different perspectives.
Always cite your sources by document name when specific information comes from a particular document."""

        # Craft the user prompt with context, history, and query
        user_prompt = f"{history_text}\n\nContext from multiple documents:\n{combined_context}\n\nQuestion: {query}"
        
        # Query OpenAI with the prepared prompts
        # response = openai_client.chat.completions.create(
        #     model=OPENAI_MODEL,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt}
        #     ],
        #     temperature=0,
        #     max_tokens=MAX_TOKEN_LIMIT
        # )
        

        # If using Ollama, uncomment the following line
        response = openai_client.chat.completions.create(
            model="llama3.2:latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=MAX_TOKEN_LIMIT
        )


        return {
            "answer": response.choices[0].message.content,
            "sources": sources
        }
        
    except Exception as e:
        logger.error(f"Error generating multi-document answer: {str(e)}")
        return {"error": f"Failed to generate answer: {str(e)}"}


# from langchain.schema.runnable import RunnablePassthrough, RunnableParallel
# from langchain.memory import ConversationBufferMemory
# from langchain.schema import messages_from_dict, messages_to_dict
# from langchain_core.output_parsers.string import StrOutputParser
# from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.runnables.base import RunnableMap
# from langchain.schema.runnable import RunnableLambda
# from langchain.prompts import PromptTemplate


# def generate_answer(query, document_id, document_path, document_type, user_id, chat_history=None):
#     """Generate a streamed answer based on document content and chat history."""
#     try:
#         # Load vector store
#         vector_store = get_document_chroma(document_id, user_id)
#         if not vector_store:
#             yield {"error": "Failed to load document data"}
#             return

#         # Setup retrievers
#         chroma_retriever = vector_store.as_retriever(
#             search_type="similarity",
#             search_kwargs={"k": 5}
#         )
#         bm25_retriever = get_bm25_retriever(document_path, document_type)
#         ensemble_retriever = EnsembleRetriever(
#             retrievers=[chroma_retriever, bm25_retriever],
#             weights=[0.5, 0.5]
#         )

#         # Setup memory
#         memory = ConversationBufferMemory(
#             memory_key="chat_history",
#             return_messages=True,
#             input_key="question",
#             output_key="answer",
#         )

#         if chat_history:
#             for message in chat_history:
#                 if message.get("is_user"):
#                     memory.chat_memory.add_user_message(message["content"])
#                 else:
#                     memory.chat_memory.add_ai_message(message["content"])

#         # Initialize LLM (with streaming)
#         llm = ChatOllama(
#             model="llama3.2:latest",
#             temperature=0,
#             max_tokens=MAX_TOKEN_LIMIT,
#             stream=True
#         )

        

#         prompt = PromptTemplate.from_template("""
#         You are a helpful assistant. Use the provided context to answer the user's question.

#         Context: {context}
#         Chat History: {chat_history}
#         Question: {question}
#         """)

#         # Step 5: Build the chain using RunnableParallel
#         chain = (
#             RunnableParallel({
#                 "context": ensemble_retriever,    # Get documents from retriever
#                 "question": RunnablePassthrough(),  # Pass question directly
#                 "chat_history": RunnableLambda(lambda x: memory.load_memory_variables({})["chat_history"])  # load memory
#             })
#             | prompt
#             | llm
#         )        

#         # Stream the answer
#         inputs = {
#             "question": query,
#         }

#         for chunk in chain.stream(inputs):
#             if chunk:
#                 yield {"content": chunk}

#         # After answer, send sources
#         source_docs = ensemble_retriever.get_relevant_documents(query)
#         sources = [doc.metadata.get("filename", "Unknown") for doc in source_docs]
#         yield {"sources": sources}

#     except Exception as e:
#         logger.error(f"Error generating answer: {str(e)}")
#         yield {"error": f"Failed to generate answer: {str(e)}"}

from langchain.schema import HumanMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

def generate_answer(query, document_id, document_path, document_type, user_id, chat_history=None):
        
        """Generate an answer to a user query based on document content with streaming"""
    
        # Get the document's ChromaDB collection
        vector_store = get_document_chroma(document_id, user_id)

        if not vector_store:
            return {"error": "Failed to load document data"}

        # Create the retriever
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        bm25_retriever = get_bm25_retriever(document_path, document_type)

        ensemble_retriever = EnsembleRetriever(retrievers=[retriever, bm25_retriever], weights=[0.5, 0.5])

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

        # Create the LLM with streaming enabled
        llm = ChatOllama(
            model="llama3.2:latest",
            temperature=0,
            max_tokens=MAX_TOKEN_LIMIT,
            streaming=True,  # Enable streaming
            callbacks=[StreamingStdOutCallbackHandler()]  # Optional: prints tokens as they are generated
        )

        # Create the conversation chain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=ensemble_retriever,
            memory=memory,
            return_source_documents=True,
            verbose=True
        )

        # Build the prompt message
        message = HumanMessage(content=query)

        # Stream the chain response
        response_stream = qa_chain.stream([message])  # Start streaming
        
        # Yield each chunk of the response as it's received
        for chunk in response_stream:
            if chunk:
                yield {"content": chunk.content}  # or chunk.text based on how the model outputs it

    
