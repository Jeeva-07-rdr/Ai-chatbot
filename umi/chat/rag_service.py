import os
import re
import math
import csv
import logging
from django.core.cache import cache

# Import LlamaIndex Core components
try:
    import llama_index.core as li_core
    from llama_index.core import Document as LlamaDocument
    from llama_index.core.node_parser import SentenceSplitter
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False

# Import document extraction libraries safely
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

logger = logging.getLogger('umi')


class RAGService:
    """
    Enterprise LlamaIndex-Powered Retrieval-Augmented Generation (RAG) Engine.
    Leverages LlamaIndex Document Node Parsers, SentenceSplitter, and Keyword Retrieval.
    """

    @staticmethod
    def extract_text(file_path, file_name):
        """
        Extracts page-annotated structured text from documents and returns LlamaIndex-ready text.
        """
        ext = os.path.splitext(file_name)[1].lower()
        logger.info(f"LlamaIndex RAG | Ingesting '{file_name}' (ext: {ext})")

        try:
            if ext == '.pdf':
                return RAGService._extract_pdf(file_path, file_name)
            elif ext == '.docx':
                return RAGService._extract_docx(file_path, file_name)
            elif ext in ['.xlsx', '.xls']:
                return RAGService._extract_excel(file_path, file_name)
            elif ext == '.csv':
                return RAGService._extract_csv(file_path, file_name)
            else:
                return RAGService._extract_plain_text(file_path, file_name)
        except Exception as e:
            logger.error(f"LlamaIndex RAG | Error extracting '{file_name}': {e}")
            return f"[Error extracting text from {file_name}: {e}]"

    @staticmethod
    def _extract_pdf(file_path, file_name):
        if not pypdf:
            return f"[Error: pypdf library is missing. Cannot extract {file_name}]"
        
        reader = pypdf.PdfReader(file_path)
        pages_text = []
        total_pages = len(reader.pages)
        
        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages_text.append(f"--- Page {idx} of {total_pages} ---\n{text}")
            else:
                pages_text.append(f"--- Page {idx} of {total_pages} ---\n[Empty or Scanned Image Page]")

        full_content = "\n\n".join(pages_text)
        logger.info(f"LlamaIndex | Parsed PDF '{file_name}': {total_pages} pages ({len(full_content)} chars)")
        return full_content

    @staticmethod
    def _extract_docx(file_path, file_name):
        if not docx:
            return f"[Error: python-docx library is missing. Cannot extract {file_name}]"

        doc = docx.Document(file_path)
        elements = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            if para.style.name.startswith('Heading 1'):
                elements.append(f"\n# {text}\n")
            elif para.style.name.startswith('Heading 2'):
                elements.append(f"\n## {text}\n")
            elif para.style.name.startswith('Heading 3'):
                elements.append(f"\n### {text}\n")
            else:
                elements.append(text)

        for t_idx, table in enumerate(doc.tables, start=1):
            elements.append(f"\n--- Table {t_idx} ---")
            for row_idx, row in enumerate(table.rows):
                row_cells = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
                elements.append("| " + " | ".join(row_cells) + " |")
                if row_idx == 0:
                    elements.append("| " + " | ".join(["---"] * len(row_cells)) + " |")

        full_content = "\n".join(elements)
        logger.info(f"LlamaIndex | Parsed DOCX '{file_name}': {len(doc.paragraphs)} paragraphs, {len(doc.tables)} tables")
        return full_content

    @staticmethod
    def _extract_excel(file_path, file_name):
        if not openpyxl:
            return f"[Error: openpyxl library is missing. Cannot extract {file_name}]"

        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheets_text = []

        for sheet in wb.worksheets:
            sheet_rows = []
            sheet_rows.append(f"--- Sheet: {sheet.title} ---")
            first_row = True
            for row in sheet.iter_rows(values_only=True):
                if any(cell is not None for cell in row):
                    formatted_row = [" " if cell is None else str(cell).strip() for cell in row]
                    sheet_rows.append("| " + " | ".join(formatted_row) + " |")
                    if first_row:
                        sheet_rows.append("| " + " | ".join(["---"] * len(formatted_row)) + " |")
                        first_row = False
            if len(sheet_rows) > 1:
                sheets_text.append("\n".join(sheet_rows))

        full_content = "\n\n".join(sheets_text)
        logger.info(f"LlamaIndex | Parsed Excel '{file_name}': {len(wb.worksheets)} sheets")
        return full_content

    @staticmethod
    def _extract_csv(file_path, file_name):
        rows = []
        encodings = ['utf-8', 'latin-1', 'cp1252']

        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                    reader = csv.reader(f)
                    for r in reader:
                        rows.append(r)
                break
            except Exception:
                continue

        if not rows:
            return f"[Empty CSV File: {file_name}]"

        md_lines = [f"--- CSV File: {file_name} ---"]
        first_row = True
        for row in rows:
            formatted_row = [cell.strip().replace('\n', ' ') for cell in row]
            md_lines.append("| " + " | ".join(formatted_row) + " |")
            if first_row:
                md_lines.append("| " + " | ".join(["---"] * len(formatted_row)) + " |")
                first_row = False

        full_content = "\n".join(md_lines)
        logger.info(f"LlamaIndex | Parsed CSV '{file_name}': {len(rows)} rows")
        return full_content

    @staticmethod
    def _extract_plain_text(file_path, file_name):
        encodings = ['utf-8', 'latin-1', 'cp1252', 'utf-16']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                    content = f.read()
                    logger.info(f"LlamaIndex | Parsed Text '{file_name}' ({len(content)} chars)")
                    return content
            except Exception:
                continue
        return f"[Error reading file text for {file_name}]"

    @staticmethod
    def create_llama_nodes(full_text, file_name, chunk_size=400, chunk_overlap=80):
        """
        Uses LlamaIndex Document & SentenceSplitter NodeParser to create semantic nodes.
        """
        if not full_text:
            return []

        if LLAMA_INDEX_AVAILABLE:
            doc = LlamaDocument(text=full_text, metadata={'file_name': file_name})
            splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            nodes = splitter.get_nodes_from_documents([doc])
            
            parsed_nodes = []
            for idx, node in enumerate(nodes, start=1):
                parsed_nodes.append({
                    'chunk_id': idx,
                    'file_name': file_name,
                    'text': node.text,
                    'word_count': len(node.text.split())
                })
            logger.info(f"LlamaIndex NodeParser | Created {len(parsed_nodes)} nodes from '{file_name}'")
            return parsed_nodes
        else:
            # Fallback sliding window node parser
            words = full_text.split()
            chunks = []
            start = 0
            while start < len(words):
                end = min(start + chunk_size, len(words))
                chunk_text = " ".join(words[start:end])
                chunks.append({
                    'chunk_id': len(chunks) + 1,
                    'file_name': file_name,
                    'text': chunk_text,
                    'word_count': len(words[start:end])
                })
                if end == len(words):
                    break
                start += (chunk_size - chunk_overlap)
            return chunks

    @staticmethod
    def retrieve_context(query, full_text, file_name, top_k=4):
        """
        LlamaIndex Context Retrieval: Performs hybrid page match & TF-IDF relevance scoring.
        """
        words = full_text.split()
        if len(words) <= 2500:
            logger.info(f"LlamaIndex | Document '{file_name}' fits context ({len(words)} words). Returning full document.")
            return full_text

        is_general_explain = any(
            kw in query.lower()
            for kw in ["explain", "summarize", "summary", "overview", "what is this", "tell me about", "details", "detail", "describe"]
        )

        nodes = RAGService.create_llama_nodes(full_text, file_name)
        if not nodes:
            return full_text

        if is_general_explain:
            logger.info(f"LlamaIndex | Explanation query detected. Returning primary nodes for '{file_name}'.")
            first_nodes = nodes[:min(top_k, len(nodes))]
            formatted = [f"--- Document: {n['file_name']} (LlamaNode #{n['chunk_id']}) ---\n{n['text']}" for n in first_nodes]
            return "\n\n".join(formatted)

        # 1. Direct Page Match Check
        page_match = re.search(r'\bpage\s*(\d+)\b', query, re.IGNORECASE)
        page_nodes = []
        if page_match:
            target_p = f"Page {page_match.group(1)}"
            page_nodes = [n for n in nodes if target_p in n['text']]

        # 2. Relevance Scoring
        query_words = re.findall(r'\w+', query.lower())
        query_words = [w for w in query_words if len(w) > 2]

        scored_nodes = []
        for node in nodes:
            t_lower = node['text'].lower()
            score = 0.0
            for qw in query_words:
                tf = t_lower.count(qw)
                if tf > 0:
                    score += (1 + math.log(tf))
            if query.lower() in t_lower:
                score += 5.0
            scored_nodes.append((score, node))

        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        top_nodes = [n for s, n in scored_nodes[:top_k] if s > 0]

        final_nodes = []
        seen_ids = set()
        for n in page_nodes + top_nodes:
            if n['chunk_id'] not in seen_ids:
                final_nodes.append(n)
                seen_ids.add(n['chunk_id'])

        if not final_nodes:
            final_nodes = nodes[:min(top_k, len(nodes))]

        formatted_retrieval = [f"--- Document: {n['file_name']} (LlamaNode #{n['chunk_id']}) ---\n{n['text']}" for n in final_nodes]
        context_output = "\n\n".join(formatted_retrieval)
        logger.info(f"LlamaIndex | Retrieved {len(final_nodes)} node(s) for query")
        return context_output

    @staticmethod
    def build_rag_prompt(user_prompt, retrieved_context):
        """
        Synthesizes a LlamaIndex-grounded prompt.
        """
        is_general_explain = any(
            kw in user_prompt.lower()
            for kw in ["explain", "summarize", "summary", "overview", "what is this", "tell me about", "details", "detail", "describe"]
        )

        if is_general_explain:
            instruction_block = (
                "INSTRUCTIONS:\n"
                "The user is asking you to explain, summarize, or describe the attached document.\n"
                "1. Provide a comprehensive, clear, and well-structured breakdown of the document context above.\n"
                "2. Summarize key points, sections, skills, background, or data presented in the document.\n"
                "3. Use Markdown headings, bullet points, and bold text for readability."
            )
        else:
            instruction_block = (
                "INSTRUCTIONS:\n"
                "1. Answer the user's question using the ATTACHED DOCUMENT CONTEXT above.\n"
                "2. If the user asks about a specific page or section (e.g., Page 3), answer directly from that page or section.\n"
                "3. Preserve original headings, key terms, code snippets, and Markdown tables where helpful.\n"
                "4. If the document is completely unrelated to the topic requested, state clearly: \"Based on the uploaded document, I could not find information regarding [topic].\""
            )

        grounded_prompt = (
            f"The following context has been extracted from the user's uploaded document(s):\n\n"
            f"=== START OF ATTACHED DOCUMENT CONTEXT ===\n"
            f"{retrieved_context}\n"
            f"=== END OF ATTACHED DOCUMENT CONTEXT ===\n\n"
            f"{instruction_block}\n\n"
            f"User Prompt: {user_prompt}"
        )
        return grounded_prompt
