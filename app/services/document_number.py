from datetime import date
from sqlalchemy.orm import Session

from app.models.document_sequence import DocumentSequence


class DocumentNumberService:
    @staticmethod
    def generate_document_number(db: Session) -> str:
        """
        Generate a unique document number in the format: DOC-YYYYMMDD-XXXX
        where XXXX is a sequential number that resets daily.
        """
        today = date.today()
        
        # Get or create sequence for today
        sequence = db.query(DocumentSequence).filter(
            DocumentSequence.sequence_date == today
        ).first()
        
        if not sequence:
            sequence = DocumentSequence(sequence_date=today, last_number=0)
            db.add(sequence)
        
        # Increment the sequence
        sequence.last_number += 1
        db.commit()
        
        # Format: DOC-YYYYMMDD-XXXX
        doc_number = f"DOC-{today.strftime('%Y%m%d')}-{sequence.last_number:04d}"
        
        return doc_number
