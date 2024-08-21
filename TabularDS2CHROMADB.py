from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.chroma import Chroma
import os
import shutil

CHROMA_PATH = "chroma2"
DATA_PATH = "data3"
os.environ['OPENAI_API_KEY'] = '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'

def main():
    generate_data_store()


def generate_data_store():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)


def load_documents():
    loader = DirectoryLoader(DATA_PATH)
    documents = loader.load()
    return documents


def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    if len(chunks) >= 11:
        document = chunks[10]
        print(document.page_content)
        print(document.metadata)
    else:
        print("Not enough chunks to access index 10.")

    return chunks


def save_to_chroma(chunks: list[Document]):
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Initialize OpenAIEmbeddings without passing the API key directly
    openai_embeddings = OpenAIEmbeddings()

    # Create a new DB from the documents.
    db = Chroma.from_documents(
        chunks, openai_embeddings, persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")



if __name__ == "__main__":
    main()