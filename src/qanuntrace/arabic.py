"""Conservative Gulf query aliases, number words, and calendar conversions."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from .core import reference_key, search_key

_GULF = {'وش':'ما','شنو':'ما','ايش':'ما','إيش':'ما','وشلون':'كيف',
         'عقب':'بعد','مو':'ليس','ابي':'أريد','أبي':'أريد','ابغى':'أريد','أبغى':'أريد'}
_UNITS = {'صفر':0,'واحد':1,'واحدة':1,'الأول':1,'الأولى':1,'اثنين':2,'اثنان':2,'اثنتين':2,
          'الثاني':2,'الثانية':2,'ثلاثة':3,'ثلاث':3,'الثالث':3,'الثالثة':3,
          'اربعة':4,'أربعة':4,'الرابع':4,'الرابعة':4,'خمسة':5,'الخامس':5,'الخامسة':5,
          'ستة':6,'السادس':6,'السادسة':6,'سبعة':7,'السابع':7,'السابعة':7,
          'ثمانية':8,'الثامن':8,'الثامنة':8,'تسعة':9,'التاسع':9,'التاسعة':9,
          'عشرة':10,'العاشر':10,'العاشرة':10}
_TENS = {'عشرون':20,'عشرين':20,'ثلاثون':30,'ثلاثين':30,'اربعون':40,'أربعون':40,
         'اربعين':40,'أربعين':40,'خمسون':50,'خمسين':50,'ستون':60,'ستين':60,
         'سبعون':70,'سبعين':70,'ثمانون':80,'ثمانين':80,'تسعون':90,'تسعين':90}

def gulf_search_key(text: str) -> str:
    terms = re.findall(r'\w+|\W+',text)
    return search_key(''.join(_GULF.get(t,t) for t in terms))

def number_word(text: str) -> int | None:
    """Parse known ordinal/cardinal units and simple unit-and-tens up to 99."""
    t=text.strip()
    if reference_key(t).isdigit(): return int(reference_key(t))
    if t in _UNITS: return _UNITS[t]
    if t in _TENS: return _TENS[t]
    parts=re.split(r'\s+و\s*|و',t)
    if len(parts)==2 and parts[0].strip() in _UNITS and parts[1].strip() in _TENS:
        return _UNITS[parts[0].strip()]+_TENS[parts[1].strip()]
    return None

@dataclass(frozen=True)
class ParsedDate:
    original: str
    calendar: str
    iso_gregorian: str
    conversion_note: str

_DATE = re.compile(r'^\s*([0-9٠-٩۰-۹]{1,4})[/-]([0-9٠-٩۰-۹]{1,2})[/-]([0-9٠-٩۰-۹]{1,4})\s*(هـ|ه|H|م|مـ|G)?\s*$')

def parse_date(value: str, calendar: str | None = None) -> ParsedDate:
    match=_DATE.match(value)
    if not match: raise ValueError('unrecognized date; clarify format/calendar')
    a,b,c=(int(reference_key(match.group(i))) for i in (1,2,3))
    if a<1000 and c>1000:
        a, c = c, a
    marker=match.group(4)
    cal=calendar or ('hijri' if marker in ('هـ','ه','H') else 'gregorian' if marker in ('م','مـ','G') else None)
    if cal not in ('hijri','gregorian'): raise ValueError('calendar ambiguous')
    if cal=='gregorian':
        return ParsedDate(value,cal,date(a,b,c).isoformat(),'Gregorian calendar')
    try:
        from hijridate import Hijri
        converted=Hijri(a,b,c).to_gregorian()
    except ImportError as exc:
        raise RuntimeError('install the hijri extra for Umm al-Qura conversion') from exc
    return ParsedDate(value,cal,date(converted.year,converted.month,converted.day).isoformat(),
                      'Umm al-Qura conversion; verify historical/official dates')
