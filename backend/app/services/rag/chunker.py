import re
from typing import List, Dict, Any

class DocumentChunkDTO:
    def __init__(self, chunk_index: int, content: str, metadata: Dict[str, Any]):
        self.chunk_index = chunk_index
        self.content = content
        self.metadata = metadata

def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    doc_metadata: Dict[str, Any] = None
) -> List[DocumentChunkDTO]:
    """
    Chunks document text using sliding window respecting paragraphs and sentence boundaries.
    """
    if not text:
        return []

    metadata_base = doc_metadata or {}
    
    # Split into logical paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    chunks: List[DocumentChunkDTO] = []
    current_chunk = ""
    current_header = ""
    chunk_idx = 0

    for paragraph in paragraphs:
        # Check if paragraph is markdown header
        if paragraph.startswith("#"):
            current_header = paragraph.split("\n")[0].strip("# ")

        if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{paragraph}".strip() if current_chunk else paragraph
        else:
            if current_chunk:
                chunks.append(
                    DocumentChunkDTO(
                        chunk_index=chunk_idx,
                        content=current_chunk,
                        metadata={
                            **metadata_base,
                            "chunk_index": chunk_idx,
                            "header_context": current_header,
                            "char_length": len(current_chunk)
                        }
                    )
                )
                chunk_idx += 1
                
                # Overlap: keep the tail of the previous chunk
                overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else ""
                current_chunk = f"{overlap_text}\n\n{paragraph}".strip() if overlap_text else paragraph
            else:
                # Single paragraph is larger than chunk_size, split by sentences
                sentences = re.split(r'(?<=[.!?]) +', paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                        current_chunk = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
                    else:
                        if current_chunk:
                            chunks.append(
                                DocumentChunkDTO(
                                    chunk_index=chunk_idx,
                                    content=current_chunk,
                                    metadata={
                                        **metadata_base,
                                        "chunk_index": chunk_idx,
                                        "header_context": current_header,
                                        "char_length": len(current_chunk)
                                    }
                                )
                            )
                            chunk_idx += 1
                        current_chunk = sentence

    if current_chunk:
        chunks.append(
            DocumentChunkDTO(
                chunk_index=chunk_idx,
                content=current_chunk,
                metadata={
                    **metadata_base,
                    "chunk_index": chunk_idx,
                    "header_context": current_header,
                    "char_length": len(current_chunk)
                }
            )
        )

    return chunks
