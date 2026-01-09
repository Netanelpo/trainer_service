from google.cloud.firestore import DocumentSnapshot

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