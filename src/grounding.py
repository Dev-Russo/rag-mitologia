"""Utilitários para vincular saídas do LLM a substrings reais do corpus."""

from __future__ import annotations

import re


def _normalized_terms(text: str) -> set[str]:
    return {
        "".join(character for character in term.casefold() if character.isalnum())
        for term in re.findall(r"\w+", text, flags=re.UNICODE)
        if len(term) >= 3
    }


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


def closest_source_quote(
    proposed_quote: str,
    source_content: str,
    *,
    concept_name: str = "",
    relation: str = "",
) -> str:
    """Seleciona uma frase literal do chunk próxima ao conceito proposto."""

    search_terms = _normalized_terms(
        f"{concept_name} {proposed_quote} {relation}"
    )
    candidates = [
        match.group().strip()
        for match in re.finditer(
            r"[^.!?]+(?:[.!?]+|$)",
            source_content,
            flags=re.DOTALL,
        )
        if match.group().strip()
    ]
    ranked = [
        (len(search_terms & _normalized_terms(candidate)), -index, candidate)
        for index, candidate in enumerate(candidates)
    ]
    if not ranked:
        raise ValueError("O chunk não contém um trecho utilizável")

    overlap, _, quote = max(ranked)
    if overlap == 0:
        raise ValueError("Nenhum trecho do chunk corresponde ao conceito")
    return quote
