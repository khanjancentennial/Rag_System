import os
import traceback
import os
import json
import io
import traceback
import pickle
import pandas as pd
import numpy as np
from pypdf import PdfReader
from docx import Document
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from .models import File, User, FaissFile
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
#from langchain.embeddings import OpenAIEmbeddings  # Change based on your embedding model
from langchain.storage import InMemoryStore
import re
import shutil
import faiss

from .serializers import FileSerializer, UserSerializer, FaissFileSerializer,QueryRequestSerializer




# Google Gemini API Key
GOOGLE_API_KEY = "AYOUR_API_KEY"

# Upload directory
UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)
vector_store = None
faiss_index = None

FAISS_INDEX_FILENAME = "index.faiss"
FAISS_PKL_FILENAME = "index.pkl"

FAISS_INDEX_DIR = os.path.join(settings.MEDIA_ROOT, "faiss_indexes")
FAISS_METADATA_DIR = os.path.join(settings.MEDIA_ROOT, "faiss_metadata")
FAISS_PKL_DIR = os.path.join(settings.MEDIA_ROOT, "faiss_pkls")  # Directory for .pkl files

os.makedirs(FAISS_PKL_DIR, exist_ok=True)  # Create the directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
# os.makedirs(FAISS_METADATA_DIR, exist_ok=True)

embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=GOOGLE_API_KEY
            )

# Generate JWT Token
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

# Register View
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = get_tokens_for_user(user)
            return Response({"message": "User created successfully", "token": token}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Login View
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = User.objects.filter(username=username).first()

        if user and user.check_password(password):
            token = get_tokens_for_user(user)
            return Response({"message": "Login successful", "token": token}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

# Refresh Token View
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                return Response({"access": str(token.access_token)}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)



def process_file(file_bytes: bytes, file_type: str) -> list:
    """Extract text from PDF, DOCX, or Excel files and split into chunks using LangChain"""
    raw_text = ""
    
    try:
        if file_type == "pdf":
            pdf_reader = PdfReader(io.BytesIO(file_bytes))
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    raw_text += text + "\n"
        elif file_type in ["doc", "docx"]:
            doc = Document(io.BytesIO(file_bytes))
            raw_text = "\n".join([para.text for para in doc.paragraphs])
        elif file_type in ["xls", "xlsx", "xlsm", "xlsb"]:
            df = pd.read_excel(io.BytesIO(file_bytes))
            raw_text = "\n".join(df.astype(str).values.flatten())
        elif file_type == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
            raw_text = "\n".join(df.astype(str).values.flatten())   
        else:
            raise ValueError("Unsupported file type. Please use PDF, DOCX, or Excel.")
    
        # Split text into chunks using LangChain
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(raw_text)

        return chunks
    except Exception as e:
        raise ValueError(f"Error processing file: {str(e)}")
    



class UploadMultipleFilesView(APIView):
    """Users can upload multiple files and create/update a combined FAISS index."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        user = request.user

        files = request.FILES.getlist("files")
        print(files)
        if not files:
            return Response({"error": "No files uploaded"}, status=400)

        try:
            processed_chunks = []
            file_records = []

            for file_obj in files:
                file_extension = file_obj.name.split(".")[-1].lower()

                # Store file in DB
                file_record = File.objects.create(user=user, file_name=file_obj.name)
                unique_id = str(file_record.id)
                file_path = os.path.join(UPLOAD_DIR, f"{unique_id}_{file_obj.name}")

                file_record.file_path = file_path
                file_record.save(update_fields=["file_path"])

                with default_storage.open(file_path, "wb") as destination:
                    for chunk in file_obj.chunks():
                        destination.write(chunk)

                with open(file_path, "rb") as f:
                    file_bytes = f.read()

                chunks = process_file(file_bytes, file_extension)

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
                file_chunks = text_splitter.split_text(" ".join(chunks))
                processed_chunks.extend(file_chunks)

                # Add metadata to track file association
                for chunk in file_chunks:
                    chunk_metadata = {"file_id": file_record.id}  # Add file ID as metadata
                    processed_chunks.append((chunk, chunk_metadata))

                file_records.append(file_record)

            # Generate FAISS index
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=GOOGLE_API_KEY
            )

            # Separate chunks and metadata
            texts = [item[0] if isinstance(item, tuple) else item for item in processed_chunks]
            metadatas = [item[1] if isinstance(item, tuple) else {} for item in processed_chunks]

            faiss_index_path = os.path.join(FAISS_INDEX_DIR, FAISS_INDEX_FILENAME)
            faiss_pkl_path = os.path.join(FAISS_PKL_DIR, FAISS_PKL_FILENAME)

            if os.path.exists(faiss_index_path) and os.path.exists(faiss_pkl_path):
                # Load existing index and update
                vector_store = FAISS.load_local(FAISS_INDEX_DIR, embeddings,allow_dangerous_deserialization=True)
                vector_store.add_texts(texts, metadatas=metadatas)
                vector_store.save_local(FAISS_INDEX_DIR)

                with open(faiss_pkl_path, "rb") as pkl_file:
                    pkl_data = pickle.load(pkl_file)

                pkl_data["docstore"] = vector_store.docstore
                pkl_data["index_to_docstore_id"] = vector_store.index_to_docstore_id

                with open(faiss_pkl_path, "wb") as pkl_file:
                    pickle.dump(pkl_data, pkl_file)

            else:
                # Create new index
                vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
                vector_store.save_local(FAISS_INDEX_DIR)
                print(f"FAISS index saved to: {os.path.abspath(FAISS_INDEX_DIR)}") #added this line
                os.rename(os.path.join(FAISS_INDEX_DIR, 'index.faiss'), faiss_index_path)

                store = vector_store.docstore
                index_to_docstore_id = vector_store.index_to_docstore_id

                pkl_data = {
                    "docstore": store,
                    "index_to_docstore_id": index_to_docstore_id,
                }
                with open(faiss_pkl_path, "wb") as pkl_file:
                    pickle.dump(pkl_data, pkl_file)

            # Create or update FaissFile record
            faiss_record, created = FaissFile.objects.get_or_create(
                defaults={
                    "faiss_index_path": faiss_index_path,
                    "index_id": len(texts), #changed this line
                },
            )
            if not created:
                faiss_record.faiss_index_path = faiss_index_path
                faiss_record.index_id = len(texts) #changed this line
                faiss_record.save()

            return Response(
                {
                    "message": "Files uploaded and combined index created/updated successfully",
                    "files": [FileSerializer(record).data for record in file_records],
                    "faiss_data": FaissFileSerializer(faiss_record).data,
                }
            )

        except ValueError as ve:
            return Response({"error": str(ve)}, status=400)
        except Exception as e:
            print("Error:", traceback.format_exc())
            return Response({"error": str(e)}, status=500)
        
class GetAllFilesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            files = File.objects.filter(user=request.user)
            if not files:
                return Response(
                    {"error": "No files are uploaded."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = FileSerializer(files, many=True)
            return Response(
                {
                    "Data": serializer.data,
                    "status": status.HTTP_200_OK,
                }
            )
        except Exception as e:
            print("Error:", traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UpdateFileView(APIView):
    """Update a file and its associated data in the FAISS index."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request, file_id, format=None):
        user = request.user
        file_obj = request.FILES.get("file")

        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_record = File.objects.get(id=file_id)
            original_file_name = file_record.file_name #save original file name
            file_extension = file_obj.name.split(".")[-1].lower()

            # Delete old file and save the new one
            old_file_path = file_record.file_path.path #get the actual file system path
            if os.path.exists(old_file_path):
                os.remove(old_file_path)

            # Generate the new filename with the file_id prefix and new filename
            new_file_name_with_id = f"{file_id}_{file_obj.name}"
            file_record.file_name = file_obj.name #set the file name to only file name in db

            # Save the file with the new name and id prefix
            file_record.file_path.save(new_file_name_with_id, file_obj)
            file_record.save()

            with file_record.file_path.open('rb') as f: #open the new file from the field.
                file_bytes = f.read()

            chunks = process_file(file_bytes, file_extension)

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            file_chunks = text_splitter.split_text(" ".join(chunks))

            # Generate FAISS index
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=GOOGLE_API_KEY
            )

            faiss_index_path = os.path.join(FAISS_INDEX_DIR, FAISS_INDEX_FILENAME)
            faiss_pkl_path = os.path.join(FAISS_PKL_DIR, FAISS_PKL_FILENAME)

            if not os.path.exists(faiss_index_path) or not os.path.exists(faiss_pkl_path):
                return Response({"error": "FAISS index or pkl file not found."}, status=status.HTTP_404_NOT_FOUND)

            vector_store = FAISS.load_local(FAISS_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)

            # Find indices to remove
            indices_to_remove = []
            for index, doc_id in vector_store.index_to_docstore_id.items():
                doc = vector_store.docstore._dict[doc_id]
                if doc.metadata.get('file_id') == file_id:
                    indices_to_remove.append(index)

            # Remove from FAISS index and docstore
            new_index_to_docstore_id = {}
            new_docstore_dict = {}
            vector_dimension = vector_store.index.reconstruct(0).shape[0]
            new_faiss_index = faiss.IndexFlatL2(vector_dimension)
            new_index = 0

            for index, doc_id in vector_store.index_to_docstore_id.items():
                if index not in indices_to_remove:
                    new_index_to_docstore_id[new_index] = doc_id
                    new_docstore_dict[doc_id] = vector_store.docstore._dict[doc_id]
                    vector = vector_store.index.reconstruct(index)
                    new_faiss_index.add(vector.reshape(1, -1))
                    new_index += 1

            # Add new chunks to the updated index
            metadatas = [{"file_id": file_id} for _ in file_chunks]
            new_vector_store = FAISS(embeddings,new_faiss_index, vector_store.docstore, new_index_to_docstore_id) #corrected line
            new_vector_store.add_texts(file_chunks, metadatas=metadatas)
            new_vector_store.save_local(FAISS_INDEX_DIR)

            # Update pkl file
            with open(faiss_pkl_path, "wb") as pkl_file:
                pickle.dump({
                    "docstore": new_vector_store.docstore,
                    "index_to_docstore_id": new_vector_store.index_to_docstore_id,
                }, pkl_file)

            return Response(
                {
                    "message": "File updated and FAISS index updated successfully",
                    "file": FileSerializer(file_record).data,
                }
            )

        except File.DoesNotExist:
            return Response({"error": f"File with ID {file_id} not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("Error:", traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class DeleteFileView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, file_id):
        try:
            file_record = File.objects.get(id=file_id)
            file_name = file_record.file_name

            faiss_index_path = os.path.join(FAISS_INDEX_DIR, FAISS_INDEX_FILENAME)
            faiss_index_pkl_file = os.path.join(FAISS_INDEX_DIR, FAISS_PKL_FILENAME)
            faiss_pkl_path = os.path.join(FAISS_PKL_DIR, FAISS_PKL_FILENAME)
            uploaded_file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file_name}") #path to uploaded file.

            if not os.path.exists(faiss_index_path) or not os.path.exists(faiss_pkl_path):
                return Response({"error": "FAISS index or pkl file not found."}, status=status.HTTP_404_NOT_FOUND)

            vector_store = FAISS.load_local(FAISS_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)

            # Find indices to remove
            indices_to_remove = []
            doc_ids_to_remove = []
            for index, doc_id in vector_store.index_to_docstore_id.items():
                doc = vector_store.docstore._dict[doc_id]
                if doc.metadata.get('file_id') == file_id:
                    indices_to_remove.append(index)
                    doc_ids_to_remove.append(doc_id)

            if not indices_to_remove:
                return Response({"error": f"No data found for file ID: {file_id} in FAISS index."}, status=status.HTTP_404_NOT_FOUND)

            # Remove from FAISS index and docstore
            new_index_to_docstore_id = {}
            new_docstore_dict = {}
            vector_dimension = vector_store.index.reconstruct(0).shape[0] #gets the dimension of the first vector.
            print(f"vector dimension: {vector_dimension}")
            new_faiss_index = faiss.IndexFlatL2(vector_dimension) # reinitialize faiss index
            new_index = 0

            for index, doc_id in vector_store.index_to_docstore_id.items():
                if index not in indices_to_remove:
                    new_index_to_docstore_id[new_index] = doc_id
                    new_docstore_dict[doc_id] = vector_store.docstore._dict[doc_id]
                    vector = vector_store.index.reconstruct(index)
                    new_faiss_index.add(vector.reshape(1, -1))
                    new_index += 1

            # Update FAISS index and pkl file
            vector_store.index = new_faiss_index
            vector_store.index_to_docstore_id = new_index_to_docstore_id
            vector_store.docstore._dict = new_docstore_dict

            vector_store.save_local(FAISS_INDEX_DIR)

            # Verification steps
            verification_vector_store = FAISS.load_local(FAISS_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
            for doc in verification_vector_store.docstore._dict.values():
                if doc.metadata.get('file_id') == file_id:
                    return Response({"error": "Verification failed: file ID still found in FAISS index."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Delete file record from database
            file_record.delete()

            # Remove original uploaded file
            if os.path.exists(uploaded_file_path):
                os.remove(uploaded_file_path)

            # Remove .faiss if no files are left
            if not File.objects.exists():
                os.remove(faiss_index_path)
                os.remove(faiss_index_pkl_file)
                os.remove(faiss_pkl_path)

            return Response({"message": f"File '{file_name}' and associated data deleted."}, status=status.HTTP_200_OK)

        except File.DoesNotExist:
            return Response({"error": f"File with ID {file_id} not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

def load_faiss_databases():
    """Loads a single FAISS index from the specified files."""
    loaded_indexes = {}  # Dictionary to store loaded index

    faiss_index_path = os.path.join(FAISS_INDEX_DIR, FAISS_INDEX_FILENAME)
    faiss_pkl_path = os.path.join(FAISS_PKL_DIR, FAISS_PKL_FILENAME)

    try:
        if not os.path.exists(faiss_index_path):
            print(f"FAISS index file not found: {faiss_index_path}")
            return {}  # Return empty dictionary if index file is missing
        if not os.path.exists(faiss_pkl_path):
            print(f"FAISS pkl file not found: {faiss_pkl_path}")
            return {} # Return empty dictionary if pkl file is missing

        # Load FAISS index
        faiss_index = faiss.read_index(faiss_index_path)

        # Load docstore and index_to_docstore_id from .pkl file
        with open(faiss_pkl_path, "rb") as pkl_file:
            pkl_data = pickle.load(pkl_file)
            #ensure pkl_data is a dictionary.
            if not isinstance(pkl_data, dict):
                raise ValueError("Pickle data is not a dictionary")

            store = pkl_data["docstore"]
            index_to_docstore_id = pkl_data["index_to_docstore_id"]

        # Initialize FAISS vector store
        vector_store = FAISS(
            index=faiss_index,
            docstore=store,
            index_to_docstore_id=index_to_docstore_id,
            embedding_function=embeddings,
        )

        loaded_indexes["single_index"] = vector_store  # Store the loaded index under a fixed key

        print(f"Loaded FAISS index from: {faiss_index_path} and {faiss_pkl_path}")

    except Exception as e:
        print(f"Error loading index: {str(e)}")

    return loaded_indexes


class QueryVectorDBView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query_text = request.data.get("query", "").strip()
        file_name = request.data.get("filename", "").strip()

        if not query_text:
            return Response({"error": "Query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            loaded_indexes = load_faiss_databases()
            if not loaded_indexes:
                return Response({"error": "FAISS index not loaded."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            vector_store = loaded_indexes.get("single_index")
            if not vector_store:
                return Response({"error": "FAISS index not found in loaded data."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            all_results = []

            if file_name:
                try:
                    file_record = File.objects.filter(file_name__icontains=file_name).first()

                    if file_record:
                        file_id = file_record.id
                        filtered_texts = []
                        filtered_metadatas = []

                        for index, doc_id in vector_store.index_to_docstore_id.items():
                            doc = vector_store.docstore._dict[doc_id]
                            if doc.metadata.get('file_id') == file_id:
                                filtered_texts.append(doc.page_content)
                                filtered_metadatas.append(doc.metadata)

                        if filtered_texts:
                            filtered_vector_store = FAISS.from_texts(filtered_texts, embeddings, metadatas=filtered_metadatas)
                            search_results = filtered_vector_store.similarity_search(query_text, k=3)
                            all_results.extend(search_results)
                        else:
                            return Response({"error": f"No data found for file: {file_name}"}, status=status.HTTP_404_NOT_FOUND)
                    else:
                        return Response({"error": f"File '{file_name}' not found."}, status=status.HTTP_404_NOT_FOUND)

                except Exception as e:
                    return Response({"error": f"Error finding file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if not all_results:
                search_results = vector_store.similarity_search(query_text, k=3)
                all_results.extend(search_results)

            if not all_results:
                return Response({"error": "No relevant results found."}, status=status.HTTP_404_NOT_FOUND)

            relevant_text = "\n".join([doc.page_content for doc in all_results])

            model = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=GOOGLE_API_KEY)
            response = model.invoke(f"Answer this based on the document: {query_text}\n\n{relevant_text}")
            print(f"Response: {response.type}")
            answer_text = str(response.content)

            if "document does not contain" in answer_text.lower() or "document does not have" in answer_text.lower() or "document lacks" in answer_text.lower():
                return Response({"answer": "Document does not contain the answer to your question."}, status=status.HTTP_200_OK)

            else:
                try:
                    # response_json = json.dumps({"answer": response})
                    # Attempt to parse the entire response as JSON
                    # json_response = json.loads(answer_text)
                    response_text = response.content if hasattr(response, "content") else str(response)
                    return Response({
                        "answer": response_text,
                        "status": status.HTTP_200_OK,
                        "question": query_text,
                        "filename": file_name,
                    }
                        )
                except json.JSONDecodeError:
                    # If not valid JSON, return as a simple JSON with the whole answer text
                    return Response(
                        {"answer": answer_text,
                         "status": status.HTTP_200_OK,
                         })

        except Exception as e:
            print(f"Error during query: {e}")
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

