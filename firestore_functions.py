from typing import Optional
from typing import Union, List

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



AgentFieldValue = Union[str, List[str]]


def set_agents_field(doc_id: str, field: str, value: AgentFieldValue) -> None:
    """
    Saves a value into agents/{doc_id}.{field}

    Value can be:
    - string
    - list of strings
    """
    # ---- Validate value ----
    if isinstance(value, list):
        if not all(isinstance(v, str) for v in value):
            raise ValueError("All items in the list must be strings")
    elif not isinstance(value, str):
        raise ValueError("Value must be a string or list of strings")

    firestore_.collection("agents").document(doc_id).set(
        {
            field: value,
            "updated_at": SERVER_TIMESTAMP,
        },
        merge=True,
    )


def get_agents_field(
        doc_id: str,
        field: str,
) -> Optional[AgentFieldValue]:
    """
    Reads agents/{doc_id}.{field}

    Returns:
    - str
    - list[str]
    - None (if missing or document does not exist)
    """
    doc_ref = firestore_.collection("agents").document(doc_id)
    doc: DocumentSnapshot = doc_ref.get()

    if not doc.exists:
        return None

    value = doc.to_dict().get(field)

    # Optional defensive validation
    if isinstance(value, list):
        if not all(isinstance(v, str) for v in value):
            return None

    if not isinstance(value, (str, list)):
        return None

    return value
