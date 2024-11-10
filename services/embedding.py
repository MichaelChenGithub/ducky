import numpy as np
import openai
import PyPDF2
import pandas as pd
from PyPDF2 import PdfFileReader
from typing import List, Dict, Tuple
import tiktoken as tkn
from openai import OpenAI
from sklearn.neighbors import NearestNeighbors
import os
from pathlib import Path
import json

class PDFSemanticSearch:
    def __init__(self, base_url='http://aitools.cs.vt.edu:7860/openai/v1', api_key="aitools"):
        """Initialize the semantic search system with OpenAI client."""
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.embedding_model = "text-embedding-3-small"
        self.chunk_size = 1500
        self.overlap = 50
        self.batch_size = 20
        self.n_neighbors = 5

    def extract_text_and_pages(self, pdf_path: str) -> List[Dict[str, any]]:
        """Extract text from PDF with page numbers."""
        documents = []
        with open(pdf_path, 'rb') as file:
            reader = PdfFileReader(file)
            current_position = 0
            
            for page_num in range(reader.getNumPages()):
                page_text = reader.getPage(page_num).extractText()
                # Store page number with each chunk
                chunks = self._chunk_text(page_text)
                for chunk in chunks:
                    documents.append({
                        'document_name': os.path.basename(pdf_path),
                        'page_number': page_num + 1,
                        'context': chunk,
                        'position': current_position
                    })
                    current_position += 1
        return documents

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks using token-based approach."""
        encoding = tkn.encoding_for_model("gpt-3.5-turbo")
        tokens = list(encoding.encode(text))

        if len(tokens) <= self.chunk_size:
            return [text]

        chunks = []
        position = 0

        while position < len(tokens):
            start_pos = max(0, position - self.overlap)
            end_pos = min(position + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start_pos:end_pos]
            chunk_text = ''.join(encoding.decode_bytes(chunk_tokens).decode('utf-8', errors='ignore'))
            chunks.append(chunk_text)
            position += self.chunk_size

        return chunks

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=[text],
            encoding_format="float"
        )
        return response.data[0].embedding

    def process_embeddings(self, pdf_path: str, embedding_csv_path: str) -> pd.DataFrame:
        """Process PDF and generate or load embeddings."""
        if os.path.exists(embedding_csv_path):
            print(f"Loading existing embeddings from {embedding_csv_path}")
            df = pd.read_csv(embedding_csv_path)
            df['embedding'] = df['embedding'].apply(eval)  # Convert string to list
            return df

        print(f"Generating new embeddings for {pdf_path}")
        documents = self.extract_text_and_pages(pdf_path)
        
        # Process embeddings in batches
        all_embeddings = []
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            batch_texts = [doc['context'] for doc in batch]
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=batch_texts,
                encoding_format="float"
            )
            
            batch_embeddings = [e.embedding for e in response.data]
            all_embeddings.extend(batch_embeddings)

        # Create DataFrame with all required columns
        df = pd.DataFrame(documents)
        df['embedding'] = all_embeddings

        # Ensure directory exists
        os.makedirs(os.path.dirname(embedding_csv_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(embedding_csv_path, index=False)
        print(f"Saved embeddings to {embedding_csv_path}")
        
        return df

    def find_relevant_chunks(self, query: str, df: pd.DataFrame, top_k: int = 3) -> List[Dict]:
        """Find the most relevant chunks for a given query."""
        # Get query embedding
        query_embedding = self.get_embedding(query)
        
        # Convert embeddings to numpy array
        embeddings_array = np.array(df['embedding'].tolist())
        
        # Initialize and fit NearestNeighbors
        nn = NearestNeighbors(n_neighbors=min(top_k, len(df)), metric='cosine')
        nn.fit(embeddings_array)
        
        # Find nearest neighbors
        distances, indices = nn.kneighbors([query_embedding])
        
        # Get relevant chunks with metadata
        relevant_chunks = []
        for idx in indices[0]:
            chunk_data = df.iloc[idx]
            relevant_chunks.append({
                'document_name': chunk_data['document_name'],
                'page_number': chunk_data['page_number'],
                'context': chunk_data['context'],
                'position': chunk_data['position']
            })
        
        return relevant_chunks