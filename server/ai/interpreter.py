"""
Form Interpreter for FormAgent

This module provides AI-powered form field analysis and interpretation
to improve form filling accuracy by understanding the context and intent
of form fields.
"""

import logging
import re
import os
from typing import Dict, Any, List, Optional, Tuple

# RAG components
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
# For local embedding fallback
import importlib.util

logger = logging.getLogger(__name__)

# Common form field patterns
EMAIL_PATTERN = re.compile(r'email|e[-_]?mail|mail', re.I)
PHONE_PATTERN = re.compile(r'phone|telephone|mobile|cell|tel', re.I)
NAME_PATTERN = re.compile(r'name|full[-_]?name', re.I)
FIRST_NAME_PATTERN = re.compile(r'first[-_]?name|given[-_]?name|fname', re.I)
LAST_NAME_PATTERN = re.compile(r'last[-_]?name|surname|family[-_]?name|lname', re.I)
ADDRESS_PATTERN = re.compile(r'address|street|addr', re.I)
CITY_PATTERN = re.compile(r'city|town|locality', re.I)
STATE_PATTERN = re.compile(r'state|province|region|county', re.I)
ZIP_PATTERN = re.compile(r'zip|postal|post[-_]?code', re.I)
COUNTRY_PATTERN = re.compile(r'country|nation', re.I)

class FormInterpreter:
    """
    AI-powered form field interpreter for FormAgent.
    
    This class is responsible for analyzing form fields and suggesting
    mappings to user data fields. It uses a combination of pattern matching,
    field attribute analysis, and RAG (Retrieval-Augmented Generation) with 
    modern LLMs for accurate form field interpretation.
    """
    
    def __init__(self, 
                 embedding_model="all-MiniLM-L6-v2", 
                 llm_model="gpt-4o-mini",
                 db_path=None,
                 use_openai=True):
        """
        Initialize the form interpreter with RAG components.
        
        Args:
            embedding_model (str): Name of embedding model to use
            llm_model (str): LLM model to use
            db_path (str): Path to store vector database
            use_openai (bool): Whether to use OpenAI API or local model
        """
        self.rag_enabled = False
        self.qa = None
        self.embeddings = None
        self.vectorstore = None
        
        try:
            # Set up paths for vector store
            if db_path is None:
                home_dir = os.path.expanduser("~")
                db_path = os.path.join(home_dir, '.formAgent', 'vectordb')
            
            self.db_path = db_path
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Initialize embeddings - try OpenAI first, fall back to HuggingFace
            if use_openai and os.environ.get("OPENAI_API_KEY"):
                logger.info("Using OpenAI embeddings")
                self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            else:
                logger.info(f"Using local HuggingFace embeddings: {embedding_model}")
                # Check if sentence-transformers is available
                if importlib.util.find_spec("sentence_transformers"):
                    self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
                else:
                    logger.warning("sentence-transformers not installed. RAG functionality disabled.")
                    return
                
            # Initialize vectorstore if it exists
            if os.path.exists(db_path) and os.path.isdir(db_path):
                logger.info(f"Loading existing vectorstore from {db_path}")
                self.vectorstore = Chroma(persist_directory=db_path, embedding_function=self.embeddings)
                
                # Initialize LLM and QA chain
                if use_openai and os.environ.get("OPENAI_API_KEY"):
                    logger.info(f"Using OpenAI model: {llm_model}")
                    llm = ChatOpenAI(model=llm_model, temperature=0.1)
                    self.qa = RetrievalQA.from_chain_type(
                        llm,
                        chain_type="stuff",
                        retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3})
                    )
                    self.rag_enabled = True
                else:
                    logger.warning("OpenAI API key not found. Using pattern matching only.")
            else:
                logger.info(f"No existing vectorstore found at {db_path}")
                
        except Exception as e:
            logger.error(f"Error initializing RAG components: {str(e)}")
            logger.info("Falling back to pattern matching only")
        
    def ingest_documents(self, docs_dir):
        """
        Ingest documents into the vector database.
        
        Args:
            docs_dir (str): Directory containing documents to ingest
            
        Returns:
            bool: Success status
        """
        try:
            if not self.embeddings:
                logger.error("Embeddings not initialized. Cannot ingest documents.")
                return False
                
            logger.info(f"Ingesting documents from {docs_dir}")
            docs = DirectoryLoader(docs_dir).load()
            
            # Split documents into chunks
            splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
            chunks = splitter.split_documents(docs)
            
            # Create and persist vectorstore
            self.vectorstore = Chroma.from_documents(
                chunks, 
                self.embeddings, 
                persist_directory=self.db_path
            )
            self.vectorstore.persist()
            
            logger.info(f"Successfully ingested {len(chunks)} chunks into vectorstore")
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting documents: {str(e)}")
            return False
            
    def interpret_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a form structure and suggest field mappings.
        
        Args:
            form_data: Dictionary containing form field information
            
        Returns:
            Dict: Interpretation results with suggested mappings
        """
        # Extract form fields
        fields = form_data.get('fields', [])
        if not fields:
            return {'mappings': [], 'confidence': 0}
        
        # Process each field to generate mappings
        mappings = []
        for field in fields:
            mapping = self._interpret_field(field)
            if mapping:
                mappings.append(mapping)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(mappings)
        
        return {
            'mappings': mappings,
            'confidence': confidence
        }
    
    def _interpret_field(self, field: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Interpret a single form field using pattern matching and RAG if available.
        
        Args:
            field: Dictionary with field properties (name, id, type, etc.)
            
        Returns:
            Dict or None: Mapping suggestion or None if no match found
        """
        field_name = field.get('name', '')
        field_id = field.get('id', '')
        field_type = field.get('type', '')
        field_label = field.get('label', '')
        field_placeholder = field.get('placeholder', '')
        
        # Combine all field attributes for better matching
        field_text = f"{field_name} {field_id} {field_label} {field_placeholder}"
        
        # Try to match using regex patterns first (fast)
        user_field, confidence = self._match_field_patterns(field_text, field_type)
        
        # If we got a high-confidence match, return it
        if user_field and confidence >= 0.8:
            return {
                'field_name': field_name or field_id,
                'field_type': field_type,
                'user_field': user_field,
                'confidence': confidence,
                'method': 'pattern_matching'
            }
        
        # If RAG is enabled and pattern matching didn't yield high confidence, try RAG
        if self.rag_enabled and self.qa:
            try:
                # Create a query for the RAG system
                query = f"""Analyze this form field and determine the best mapping:
                Name: {field_name}
                ID: {field_id}
                Type: {field_type}
                Label: {field_label}
                Placeholder: {field_placeholder}
                
                Return only a single field mapping as one of these values: first_name, last_name, 
                full_name, email, phone, address_street, address_city, address_state, address_zip, 
                address_country, or other descriptive field name if none match."""
                
                # Query the RAG system
                result = self.qa.invoke(query)
                
                # Extract the answer - should be a simple field name
                rag_field = result.get('result', '').strip().lower()
                
                # Only use the RAG result if it returned a valid field name
                if rag_field and len(rag_field) < 50:  # Sanity check - field names should be short
                    return {
                        'field_name': field_name or field_id,
                        'field_type': field_type,
                        'user_field': rag_field,
                        'confidence': 0.85,  # RAG typically provides good quality answers
                        'method': 'rag'
                    }
            except Exception as e:
                logger.error(f"RAG interpretation error: {str(e)}")
        
        # If pattern matching found something with lower confidence, return that
        if user_field:
            return {
                'field_name': field_name or field_id,
                'field_type': field_type,
                'user_field': user_field,
                'confidence': confidence,
                'method': 'pattern_matching'
            }
        
        # No match found
        return None
    
    def _match_field_patterns(self, field_text: str, field_type: str) -> Tuple[Optional[str], float]:
        """
        Match field text against common patterns.
        
        Args:
            field_text: Combined text from field attributes
            field_type: HTML input type
            
        Returns:
            Tuple[str, float]: Suggested user field and confidence score
        """
        # Check for email fields
        if field_type == 'email' or EMAIL_PATTERN.search(field_text):
            return 'email', 0.9
        
        # Check for phone fields
        if field_type == 'tel' or PHONE_PATTERN.search(field_text):
            return 'phone', 0.9
        
        # Check for name fields
        if FIRST_NAME_PATTERN.search(field_text):
            return 'first_name', 0.9
        
        if LAST_NAME_PATTERN.search(field_text):
            return 'last_name', 0.9
        
        if NAME_PATTERN.search(field_text):
            return 'full_name', 0.8
        
        # Check for address fields
        if ADDRESS_PATTERN.search(field_text):
            return 'address_street', 0.8
        
        if CITY_PATTERN.search(field_text):
            return 'address_city', 0.8
        
        if STATE_PATTERN.search(field_text):
            return 'address_state', 0.8
        
        if ZIP_PATTERN.search(field_text):
            return 'address_zip', 0.9
        
        if COUNTRY_PATTERN.search(field_text):
            return 'address_country', 0.9
            
        # No match found
        return None, 0.0
    
    def _calculate_confidence(self, mappings: List[Dict[str, Any]]) -> float:
        """
        Calculate overall confidence for the form interpretation.
        
        Args:
            mappings: List of field mappings
            
        Returns:
            float: Overall confidence score between 0 and 1
        """
        if not mappings:
            return 0.0
        
        # Calculate average confidence of all mappings
        total_confidence = sum(m['confidence'] for m in mappings)
        return total_confidence / len(mappings)
        
    def enhance_with_ai(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use RAG to enhance form interpretation beyond pattern matching.
        
        This method leverages the Retrieval-Augmented Generation system to
        provide more accurate form field interpretations based on context.
        
        Args:
            form_data: Dictionary containing form field information
            
        Returns:
            Dict: Enhanced interpretation results
        """
        if not self.rag_enabled:
            logger.info("RAG not enabled. Falling back to basic interpretation.")
            return self.interpret_form(form_data)
            
        try:
            # Extract form fields and form context
            fields = form_data.get('fields', [])
            form_url = form_data.get('url', '')
            form_title = form_data.get('title', '')
            
            if not fields:
                return {'mappings': [], 'confidence': 0}
            
            # Create a context string for the entire form
            form_context = f"Form URL: {form_url}\nForm Title: {form_title}\n"
            form_context += f"Number of fields: {len(fields)}\n"
            
            # Generate field descriptions
            field_descriptions = []
            for i, field in enumerate(fields):
                desc = f"Field {i+1}: "
                desc += f"name='{field.get('name', '')}', "
                desc += f"id='{field.get('id', '')}', "
                desc += f"type='{field.get('type', '')}', "
                desc += f"label='{field.get('label', '')}', "
                desc += f"placeholder='{field.get('placeholder', '')}'"
                field_descriptions.append(desc)
            
            form_context += "\n".join(field_descriptions)
            
            # Process each field to generate mappings with RAG context
            mappings = []
            for field in fields:
                # First try the regular interpretation
                mapping = self._interpret_field(field)
                
                # If we have a low confidence or no match, use RAG with full form context
                if not mapping or mapping['confidence'] < 0.7:
                    # Build a query that includes the form context
                    field_name = field.get('name', '')
                    field_id = field.get('id', '')
                    field_type = field.get('type', '')
                    field_label = field.get('label', '')
                    field_placeholder = field.get('placeholder', '')
                    
                    query = f"""Based on the following form context, what user data field should be used 
                    for the field with name='{field_name}', id='{field_id}', type='{field_type}', 
                    label='{field_label}', placeholder='{field_placeholder}'?
                    
                    FORM CONTEXT:
                    {form_context}
                    
                    Return only a single field name as one of: first_name, last_name, full_name, email, 
                    phone, address_street, address_city, address_state, address_zip, address_country, 
                    or other descriptive field name if none match."""
                    
                    try:
                        # Query the RAG system
                        result = self.qa.invoke(query)
                        rag_field = result.get('result', '').strip().lower()
                        
                        if rag_field and len(rag_field) < 50:
                            mapping = {
                                'field_name': field_name or field_id,
                                'field_type': field_type,
                                'user_field': rag_field,
                                'confidence': 0.9,  # Higher confidence with full context
                                'method': 'contextual_rag'
                            }
                    except Exception as e:
                        logger.error(f"Contextual RAG error: {str(e)}")
                
                if mapping:
                    mappings.append(mapping)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(mappings)
            
            return {
                'mappings': mappings,
                'confidence': confidence,
                'rag_enabled': True
            }
            
        except Exception as e:
            logger.error(f"Error in enhance_with_ai: {str(e)}")
            return self.interpret_form(form_data)