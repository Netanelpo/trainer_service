from typing import Optional

from google.cloud.firestore import DocumentSnapshot
from google.cloud.firestore import SERVER_TIMESTAMP

from infra import firestore_


def get_agent_instructions(doc_id: str) -> str:
    doc_ref = firestore_.collection("agents").document(doc_id)
    doc: DocumentSnapshot = doc_ref.get()

    if not doc.exists:
        raise ValueError(f"Instructions not found: {doc_id}")

    data = doc.to_dict()
    instructions = data.get("instructions")

    # Expecting a non-empty list of strings
    if not isinstance(instructions, list) or not instructions:
        raise ValueError(f"Invalid instructions list in document: {doc_id}")

    first = instructions[0]

    if not isinstance(first, str) or not first.strip():
        raise ValueError(f"First instruction is invalid in document: {doc_id}")
    print(first)
    return first


def set_last_response_id(doc_id: str, last_response_id: str) -> None:
    """
    Saves last_response_id into agents/{doc_id}
    """
    firestore_.collection("agents").document(doc_id).set(
        {
            "last_response_id": last_response_id,
            "updated_at": SERVER_TIMESTAMP,
        },
        merge=True,  # do not overwrite other fields
    )


def get_last_response_id(doc_id: str) -> Optional[str]:
    """
    Reads last_response_id from agents/{doc_id}
    Returns None if missing.
    """
    doc_ref = firestore_.collection("agents").document(doc_id)
    doc: DocumentSnapshot = doc_ref.get()

    if not doc.exists:
        return None

    return doc.to_dict().get("last_response_id")
