"""
rag.py — VitalWatch RAG Pipeline

Knowledge base construction (in priority order):
  1. PDF files in data/guidelines/ — loaded with pypdf, chunked with
     RecursiveCharacterTextSplitter (chunk_size=800, overlap=100)
  2. 16 hard-coded seed documents — always included, guarantee minimum
     coverage even if PDF loading fails or the directory is empty

Index persistence:
  - FAISS index is saved to data/faiss_index/ after first build
  - Subsequent startups load from disk (fast, no re-embedding needed)
  - If the saved index is stale / incompatible, it is rebuilt automatically

Run `python data/guidelines/generate_guidelines.py` to regenerate PDFs.
"""
import os
import time
import logging
import re
from typing import Optional

from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class RAGPipeline:
    def __init__(self, groq_api_key: Optional[str] = None):
        if not groq_api_key:
            raise ValueError("Groq API key is required to initialize RAGPipeline.")

        self.api_key  = groq_api_key
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.index_path      = os.path.join(self.base_dir, "data", "faiss_index_groq")
        self.guidelines_path = os.path.join(self.base_dir, "data", "guidelines")

        # LLM & embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            groq_api_key=self.api_key,
        )

        # Build the full document set (PDFs + hardcoded seeds)
        self.documents = self._build_knowledge_base()
        logging.info(
            f"Knowledge base ready: {len(self.documents)} chunks "
            f"(from PDFs + {len(self._seed_documents())} seed docs)"
        )

        # Load or rebuild the FAISS vector index
        index_file = os.path.join(self.index_path, "index.faiss")
        if os.path.exists(index_file):
            try:
                self.vectorstore = FAISS.load_local(
                    self.index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                logging.info(f"FAISS index loaded from {self.index_path}")
            except Exception as exc:
                logging.warning(f"Failed to load FAISS index ({exc}). Rebuilding…")
                self._build_index()
        else:
            self._build_index()

    # ------------------------------------------------------------------
    # Knowledge-base construction
    # ------------------------------------------------------------------

    def _load_pdfs(self) -> list[Document]:
        """
        Scan data/guidelines/ for PDF files, extract text with pypdf,
        and split into overlapping chunks with RecursiveCharacterTextSplitter.
        Returns an empty list (gracefully) if pypdf is unavailable or no
        PDFs are present.
        """
        chunks: list[Document] = []

        if not os.path.isdir(self.guidelines_path):
            logging.warning(f"Guidelines directory not found: {self.guidelines_path}")
            return chunks

        try:
            from pypdf import PdfReader
        except ImportError:
            logging.warning("pypdf not installed — skipping PDF loading. Run: pip install pypdf")
            return chunks

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        pdf_files = sorted(
            f for f in os.listdir(self.guidelines_path)
            if f.lower().endswith(".pdf") and not f.startswith(".")
        )

        if not pdf_files:
            logging.warning(f"No PDF files found in {self.guidelines_path}")
            return chunks

        for fname in pdf_files:
            fpath = os.path.join(self.guidelines_path, fname)
            try:
                reader = PdfReader(fpath)
                full_text = "\n\n".join(
                    (page.extract_text() or "").strip()
                    for page in reader.pages
                )
                if len(full_text.strip()) < 100:
                    logging.warning(f"Skipping {fname}: extracted text too short ({len(full_text)} chars)")
                    continue

                doc_chunks = splitter.create_documents(
                    [full_text],
                    metadatas=[{"source": fname.replace("_", " ").replace(".pdf", ""), "file": fname}],
                )
                chunks.extend(doc_chunks)
                logging.info(f"Loaded {fname}: {len(reader.pages)} pages → {len(doc_chunks)} chunks")

            except Exception as exc:
                logging.error(f"Failed to load {fname}: {exc}")

        return chunks

    def _seed_documents(self) -> list[Document]:
        """
        16 hard-coded clinical documents — guaranteed baseline that is always
        included regardless of PDF availability.
        """
        return [
            Document(page_content="Intraoperative hypotension (IOH) is generally defined as a mean arterial pressure (MAP) falling below 65 mmHg during surgery. It is a critical event requiring rapid intervention to ensure organ perfusion.", metadata={"source": "Definition of IOH"}),
            Document(page_content="One of the primary clinical causes of intraoperative hypotension is spinal anesthesia. The resultant sympathetic blockade causes vasodilation and subsequent drops in blood pressure.", metadata={"source": "Causes: Spinal Anesthesia"}),
            Document(page_content="General anesthesia agents commonly cause vasodilation and myocardial depression, which can result in reduced systemic vascular resistance and intraoperative hypotension.", metadata={"source": "Causes: General Anesthesia"}),
            Document(page_content="Significant blood loss or hemorrhage during surgical procedures reduces circulating blood volume, directly lowering the mean arterial pressure and causing IOH.", metadata={"source": "Causes: Blood Loss"}),
            Document(page_content="Vasodilation induced by anesthetic drugs, patient positioning, or anaphylaxis can cause profound hypotension by dropping systemic vascular resistance rather than volume depletion.", metadata={"source": "Causes: Vasodilation"}),
            Document(page_content="Elderly patients have stiffer vasculature and impaired autonomic reflexes, heavily increasing their risk of developing severe intraoperative hypotension under anesthesia.", metadata={"source": "Risk Factors: Elderly Patients"}),
            Document(page_content="A high American Society of Anesthesiologists (ASA) physical status score indicates higher baseline morbidity, serving as a primary risk factor for adverse intraoperative hemodynamic events including IOH.", metadata={"source": "Risk Factors: High ASA"}),
            Document(page_content="Pre-existing hypertension can ironically predispose to intraoperative hypotension because these patients require higher baseline pressures and are highly sensitive to the vasodilatory effects of anesthetic drugs.", metadata={"source": "Risk Factors: Pre-existing Hypertension"}),
            Document(page_content="Patients with diabetes often suffer from autonomic neuropathy, impairing their physiological ability to compensate for sudden hemodynamic shifts and increasing risk of IOH.", metadata={"source": "Risk Factors: Diabetes"}),
            Document(page_content="The primary and most rapid treatment for profound IOH involves vasopressors. Common agents include phenylephrine for pure alpha-agonism, ephedrine for mixed alpha/beta, and norepinephrine for severe refractory cases.", metadata={"source": "Treatment: Vasopressors"}),
            Document(page_content="Intravenous (IV) fluids remain a critical treatment modality for IOH, especially when the hypotension is volume-driven due to fasting, blood loss, or insensible fluid losses during surgery.", metadata={"source": "Treatment: IV Fluids"}),
            Document(page_content="If a patient experiences IOH without volume depletion or surgical bleeding, the anesthesiologist may need to reduce the depth of anesthesia to reverse the drug-induced vasodilation and cardiac depression.", metadata={"source": "Treatment: Reduce Anesthetic Depth"}),
            Document(page_content="Prevention strategies for IOH include pre-loading intravenous fluids prior to inducing anesthesia, particularly before spinal blocks, to maintain adequate preload.", metadata={"source": "Prevention: Fluid Pre-loading"}),
            Document(page_content="Goal-directed fluid therapy uses dynamic variables like pulse pressure variation or stroke volume variation to optimize fluid management and actively prevent IOH.", metadata={"source": "Prevention: Goal-Directed Therapy"}),
            Document(page_content="Prolonged intraoperative hypotension leads to severe post-operative consequences. The most notable outcomes include acute kidney injury (AKI), myocardial injury, stroke, and an overall increased 30-day mortality risk.", metadata={"source": "Consequences of IOH"}),
            Document(page_content="The VitalDB dataset provides high-resolution intraoperative vital signs, including MAP and HR. The ML model utilises derived features, trends, and variances from this dataset to predict IOH events before they manifest.", metadata={"source": "VitalDB Dataset & ML Model"}),
        ]

    def _build_knowledge_base(self) -> list[Document]:
        """Merge PDF chunks with seed documents. Seed docs are always included."""
        pdf_chunks = self._load_pdfs()
        seed_docs  = self._seed_documents()
        all_docs   = pdf_chunks + seed_docs
        logging.info(
            f"Knowledge base: {len(pdf_chunks)} PDF chunks + "
            f"{len(seed_docs)} seed docs = {len(all_docs)} total"
        )
        return all_docs

    def _build_index(self):
        logging.info(f"Building FAISS index from {len(self.documents)} documents…")
        os.makedirs(self.index_path, exist_ok=True)
        self.vectorstore = FAISS.from_documents(self.documents, self.embeddings)
        self.vectorstore.save_local(self.index_path)
        logging.info(f"FAISS index saved to {self.index_path}")

    # Public alias used by existing tests / main.py
    def build_index(self):
        self._build_index()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, question: str, patient_context: Optional[str] = None):
        start = time.time()

        retrieved_docs = self.vectorstore.similarity_search(question, k=4)
        context_text   = "\n\n".join(
            f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
            for doc in retrieved_docs
        )
        sources = [doc.metadata.get("source", "Unknown") for doc in retrieved_docs]

        system_msg = (
            "You are a clinical anesthesiology assistant. "
            "Answer based only on the provided context. "
            "Be precise and cite sources."
        )

        full_query = question
        if patient_context:
            full_query = f"Patient Context: {patient_context}\n\nQuestion: {question}"

        prompt = f"{system_msg}\n\nContext:\n{context_text}\n\n{full_query}"

        from langchain_core.messages import HumanMessage
        response = self.llm.invoke([HumanMessage(content=prompt)])
        answer   = response.content

        latency_ms = (time.time() - start) * 1000
        return answer, sources, latency_ms

    # ------------------------------------------------------------------
    # Faithfulness evaluation
    # ------------------------------------------------------------------

    def evaluate_response(self, question: str, answer: str, retrieved_docs: list) -> dict:
        if not retrieved_docs or not answer:
            return {
                "faithfulness_score": 0.0,
                "retrieval_count": len(retrieved_docs),
                "estimated_hallucination_risk": "high",
            }

        combined_context = " ".join(d.page_content.lower() for d in retrieved_docs)
        words_in_answer  = set(re.findall(r"\b[a-z]{2,}\b", answer.lower()))

        stop_words = {
            "the", "and", "for", "with", "are", "but", "not", "you", "all",
            "any", "can", "has", "was", "that", "from", "this", "they", "have",
            "been", "one", "were",
        }
        relevant_words = words_in_answer - stop_words
        match_count    = sum(1 for w in relevant_words if w in combined_context)

        faithfulness_score = (
            match_count / len(relevant_words) if relevant_words else 1.0
        )

        if faithfulness_score > 0.6:
            risk = "low"
        elif faithfulness_score > 0.3:
            risk = "medium"
        else:
            risk = "high"

        return {
            "faithfulness_score": float(faithfulness_score),
            "retrieval_count": len(retrieved_docs),
            "estimated_hallucination_risk": risk,
        }
