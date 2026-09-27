import json
from hashlib import sha256

from qanuntrace.config import doctor, load_config, make_store


def test_configured_sqlite(tmp_path, monkeypatch):
    from sqlalchemy import Column, MetaData, String, Table, create_engine
    path = tmp_path / 'records.db'
    engine = create_engine('sqlite+pysqlite:///' + str(path))
    metadata = MetaData()
    table = Table('legal_records', metadata, *[Column(k, String) for k in
                  ('source_id','instrument_id','edition_id','kind','article_number','original_text',
                   'source_uri','sha256_utf8','valid_from','valid_to')])
    metadata.create_all(engine)
    exact = 'نص تجريبي'
    with engine.begin() as conn:
        conn.execute(table.insert(), {'source_id': 's1','instrument_id': 'i1','edition_id': 'v1',
                     'kind': 'article','article_number': '1','original_text': exact,'source_uri': 'fixture:local',
                     'sha256_utf8': sha256(exact.encode()).hexdigest(),'valid_from': '2025-01-01',
                     'valid_to': '2027-01-01'})
    config = {'backend': 'sqlalchemy','database_url_env': 'TEST_DB_URL','table': 'legal_records',
                  'fields': {'source_id': 'source_id','instrument_id': 'instrument_id','edition_id': 'edition_id',
                              'kind': 'kind','reference': 'article_number','exact_text': 'original_text',
                              'source_uri': 'source_uri','source_hash': 'sha256_utf8',
                              'effective_from': 'valid_from','effective_to': 'valid_to'}}
    config_path = tmp_path / 'config.json'
    config_path.write_text(json.dumps(config))
    monkeypatch.setenv('TEST_DB_URL', 'sqlite+pysqlite:///' + str(path))
    assert make_store(load_config(config_path)).get('s1').exact_text == exact
    assert 'sample_record_valid' in doctor(config)
