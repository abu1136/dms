from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.document_sequence import DocumentSequence


class DocumentNumberService:
    @staticmethod
    def generate_document_number(db: Session) -> str:
        """
        Generate a unique document number in the format: DOC-YYYYMMDD-XXXX
        where XXXX is a sequential number that resets daily.
        """
        today = date.today()
        attempts = 0
        
        while attempts < 3:
            try:
                sequence = db.execute(
                    select(DocumentSequence)
                    .where(DocumentSequence.sequence_date == today)
                    .with_for_update()
                ).scalar_one_or_none()
                
                if not sequence:
                    sequence = DocumentSequence(sequence_date=today, last_number=0)
                    db.add(sequence)
                    db.flush()
                
                sequence.last_number += 1
                db.flush()
                last_number = sequence.last_number
                
                doc_number = f"DOC-{today.strftime('%Y%m%d')}-{last_number:04d}"
                return doc_number
            except IntegrityError:
                db.rollback()
                attempts += 1
        
        raise RuntimeError("Failed to generate document number after retries")
