# backend/app/main.py
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import logging
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.constitutional_ai.base import ConstitutionalChain
from langchain.chains.constitutional_ai.models import ConstitutionalPrinciple
import tempfile

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask application
app = Flask(__name__)

# OpenAI API Key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY not found in environment variables.")
    # Consider raising an exception or handling this gracefully
    OPENAI_API_KEY = "dummy_key_for_local_testing" # Replace with actual key or handle appropriately

# Initialize Langchain components (initialized lazily within the route)
embeddings = None
vectorstore = None
qa_chain = None

def load_and_index_resume(pdf_file_path: str):
    """
    Loads a PDF resume, splits it into chunks, and indexes it into a Chroma vector store.

    Args:
        pdf_file_path: The path to the PDF resume file.

    Returns:
        Chroma: A Chroma vector store containing the indexed resume content.
    """
    logging.info(f"Loading and indexing resume from: {pdf_file_path}")
    try:
        loader = PyPDFLoader(pdf_file_path)
        documents = loader.load()
    except Exception as e:
        logging.error(f"Error loading PDF: {e}")
        return None

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)

    global embeddings
    if embeddings is None:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    global vectorstore
    vectorstore = Chroma.from_documents(texts, embeddings)
    logging.info("Resume indexed successfully.")
    return vectorstore

def create_qa_chain(vector_store: Chroma):
    """
    Creates a RetrievalQA chain using the provided vector store and OpenAI LLM.

    Args:
        vector_store: The Chroma vector store containing the resume index.

    Returns:
        RetrievalQA: A Langchain RetrievalQA chain.
    """
    logging.info("Creating RetrievalQA chain.")
    llm = OpenAI(openai_api_key=OPENAI_API_KEY)
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vector_store.as_retriever())
    logging.info("RetrievalQA chain created.")
    return qa

def analyze_resume(qa_chain: RetrievalQA, query: str):
    """
    Analyzes the resume using the RetrievalQA chain and a provided query.

    Args:
        qa_chain: The Langchain RetrievalQA chain.
        query: The question or instruction for analyzing the resume.

    Returns:
        str: The analysis result from the LLM.
    """
    logging.info(f"Analyzing resume with query: {query}")
    try:
        result = qa_chain({"query": query})
        return result["result"]
    except Exception as e:
        logging.error(f"Error during resume analysis: {e}")
        return "Could not analyze the resume at this time."

def create_constitutional_chain(llm: OpenAI):
    """
    Creates a ConstitutionalChain for AI validation of the analysis.

    Args:
        llm: An OpenAI language model instance.

    Returns:
        ConstitutionalChain: A Langchain ConstitutionalChain.
    """
    logging.info("Creating ConstitutionalChain for AI validation.")
    # Define principles for helpful and harmless output
    principles = [
        ConstitutionalPrinciple(name="Helpful", text="The AI should provide helpful and relevant feedback."),
        ConstitutionalPrinciple(name="Harmless", text="The AI should avoid generating harmful, unethical, or biased feedback."),
    ]
    constitutional_chain = ConstitutionalChain.from_llm(llm=llm, constitutional_principles=principles)
    logging.info("ConstitutionalChain created.")
    return constitutional_chain

def validate_analysis(constitutional_chain: ConstitutionalChain, analysis_result: str):
    """
    Validates the AI-generated analysis using the ConstitutionalChain.

    Args:
        constitutional_chain: The Langchain ConstitutionalChain.
        analysis_result: The raw analysis result from the LLM.

    Returns:
        str: The validated analysis result.
    """
    logging.info("Validating AI analysis.")
    try:
        validated_response = constitutional_chain.run(analysis_result)
        logging.info(f"Validated analysis: {validated_response}")
        return validated_response
    except Exception as e:
        logging.error(f"Error during analysis validation: {e}")
        return analysis_result # Return the original if validation fails

@app.route('/analyze', methods=['POST'])
def analyze_resume_route():
    """
    API endpoint for uploading a resume and receiving analysis.
    """
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400

    resume_file = request.files['resume']
    if resume_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if resume_file and allowed_file(resume_file.filename):
        # Use tempfile to get a temporary directory and create a temporary file path
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, resume_file.filename)
        logging.info(f"Resume saved to temporary path: {temp_file_path}")

        try:
            resume_file.save(temp_file_path)
            logging.info(f"Resume successfully saved to: {temp_file_path}")

            # Load and index the resume
            vector_db = load_and_index_resume(temp_file_path)
            os.remove(temp_file_path) # Clean up temporary file

            if vector_db:
                global qa_chain
                if qa_chain is None:
                    qa_chain = create_qa_chain(vector_db)

                # Define analysis queries
                section_presence_query = "List the key sections present in the resume (e.g., Education, Experience, Skills, Summary)."
                improvement_suggestions_query = "Provide specific and actionable suggestions to improve this resume for a software engineering role."

                section_presence_result = analyze_resume(qa_chain, section_presence_query)
                improvement_suggestions_result = analyze_resume(qa_chain, improvement_suggestions_query)

                # AI Validation
                llm = OpenAI(openai_api_key=OPENAI_API_KEY)
                constitutional_qa_chain = create_constitutional_chain(llm)
                validated_suggestions = validate_analysis(constitutional_qa_chain, improvement_suggestions_result)

                return jsonify({
                    "sections_present": section_presence_result,
                    "improvement_suggestions": validated_suggestions
                })
            else:
                return jsonify({"error": "Failed to process the resume file."}), 500

        except Exception as e:
            logging.error(f"Error processing resume: {e}")
            return jsonify({"error": f"Error processing resume: {e}"}), 500

        finally:
            # Ensure temporary file is removed even if errors occur
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    return jsonify({"error": "Invalid file format. Only PDF files are allowed."}), 400

def allowed_file(filename):
    """
    Checks if the file extension is allowed (only PDF in this case).
    """
    return filename.lower().endswith('.pdf')

if __name__ == '__main__':
    app.run(debug=True, port=5000)