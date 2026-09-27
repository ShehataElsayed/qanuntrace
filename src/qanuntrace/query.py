"""Conservative Arabic query understanding and ambiguity detection."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from .core import reference_key, search_key

Intent = Literal['article_lookup','compare_versions','judgment_lookup','analysis','unknown']
_NUM = r'[0-9٠-٩۰-۹]+'
_ORDINALS = {'الأولى':'1','الأول':'1','الثانية':'2','الثاني':'2','الثالثة':'3',
             'الثالث':'3','الرابعة':'4','الرابع':'4','الخامسة':'5','الخامس':'5',
             'السادسة':'6','السادس':'6','السابعة':'7','السابع':'7','الثامنة':'8',
             'الثامن':'8','التاسعة':'9','التاسع':'9','العاشرة':'10','العاشر':'10'}
_ARTICLE = re.compile(r'(?:الماد[ةه]|مادة|م\s*|article\s*)\s*(?:\(\s*)?('+_NUM+r'|'
                      +'|'.join(_ORDINALS)+r')(?:\s*\))?',re.IGNORECASE)

@dataclass(frozen=True)
class ParsedQuery:
    original: str
    search_text: str
    intent: Intent
    article_refs: tuple[str,...]
    instrument_ids: tuple[str,...]
    clarification: str | None
    notes: tuple[str,...]

def parse_query(text: str, aliases: dict[str,str] | None = None) -> ParsedQuery:
    if not text.strip():
        return ParsedQuery(text,'','unknown',(),(), 'Please provide a legal question.',('empty_query',))
    aliases = aliases or {}
    refs = tuple(dict.fromkeys(reference_key(_ORDINALS.get(m.group(1),m.group(1)))
                               for m in _ARTICLE.finditer(text)))
    normalized = search_key(text)
    ids = tuple(dict.fromkeys(instrument_id for alias,instrument_id in aliases.items()
                              if search_key(alias) in normalized))
    if re.search(r'\b(?:حكم|قضية|صك|محكمة)\b',text): intent: Intent = 'judgment_lookup'
    elif re.search(r'قارن|مقارنة|التعديل|الاصدار|الإصدار',text): intent = 'compare_versions'
    elif refs: intent = 'article_lookup'
    else: intent = 'analysis'
    notes = []
    if normalized != text.strip().lower(): notes.append('normalized_for_search_only')
    if len(refs)>1: notes.append('multiple_article_references')
    if len(ids)>1: notes.append('multiple_instrument_aliases')
    clarification = None
    if len(refs)>1 and intent == 'article_lookup':
        clarification = 'Which article do you mean?'
    elif len(ids)>1:
        clarification = 'Which law or regulation do you mean?'
    elif refs and not ids:
        clarification = 'Which law or regulation contains this article?'
    return ParsedQuery(text,normalized,intent,refs,ids,clarification,tuple(notes))
