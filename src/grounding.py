"""Utilitários para vincular saídas do LLM a substrings reais do corpus."""

from __future__ import annotations


def canonical_source_quote(proposed_quote: str, source_content: str) -> str:
    """Retorna a substring original ignorando apenas diferenças tipográficas."""

    def normalized_with_positions(text: str) -> tuple[str, list[int]]:
        characters: list[str] = []
        positions: list[int] = []
        for index, character in enumerate(text):
            for folded in character.casefold():
                if folded.isalnum():
                    characters.append(folded)
                    positions.append(index)
        return "".join(characters), positions

    proposed, _ = normalized_with_positions(proposed_quote)
    source, positions = normalized_with_positions(source_content)
    if not proposed:
        raise ValueError("A citação proposta não contém texto")

    start = source.find(proposed)
    if start < 0:
        raise ValueError("A citação não corresponde literalmente ao chunk")

    source_start = positions[start]
    source_end = positions[start + len(proposed) - 1] + 1
    return source_content[source_start:source_end].strip()
