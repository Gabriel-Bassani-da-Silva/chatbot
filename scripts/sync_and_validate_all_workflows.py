import json
import os
import sys
import subprocess
import uuid

sys.stdout.reconfigure(encoding='utf-8')

ACTIVE_WORKFLOW_FILES = {
    'vKrMSyZ4jMDtbjW7': 'workflows/Agente RAG Fatec.json',
    'IQ2aYo90KeGQlR4G': 'workflows/subworkflows/Comando _agenda — Google Calendar.json',
    'PUcBETeUWZ8fC251': 'workflows/subworkflows/Comando _cardapio — Google Sheets.json',
    'B34exXTSXsfHnF8O': 'workflows/subworkflows/Processar anexos — Normalização multimodal Chatwoot.json',
    'bf1MReoTnd7QMPBC': 'workflows/subworkflows/Subworkflow - Normalização multimodal Chatwoot.json',
    'gdrive_rag_sync1': 'workflows/Sincronização RAG — Google Drive para PGVector.json',
    'rag_model_change_sync': 'workflows/RAG — Monitor de Mudança de Modelo de Embedding.json'
}

def query_db(sql):
    cmd = ['docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8', '-i', 'chatbot_n8n-postgres-1', 'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A']
    res = subprocess.run(cmd, input=sql.encode('utf-8'), capture_output=True)
    return res.stdout.decode('utf-8', errors='replace'), res.stderr.decode('utf-8', errors='replace')

def sync_and_publish_workflow(wf_id, filepath):
    print(f"\n--- Syncing & Publishing {wf_id} from {filepath} ---")
    with open(filepath, 'r', encoding='utf-8') as f:
        wf = json.load(f)

    name = wf.get('name', '')
    nodes = wf.get('nodes', [])
    connections = wf.get('connections', {})
    settings = wf.get('settings', {})
    meta = wf.get('meta', {})
    new_version_id = str(uuid.uuid4())

    # Validate structure locally first
    node_names = set(n.get('name') for n in nodes)
    missing_sources = []
    missing_targets = []
    for s_node, outputs in connections.items():
        if s_node not in node_names:
            missing_sources.append(s_node)
        for _, c_groups in outputs.items():
            for c_group in c_groups:
                for c in c_group:
                    t_node = c.get('node')
                    if t_node not in node_names:
                        missing_targets.append((s_node, t_node))

    if missing_sources or missing_targets:
        print(f"ERROR: Local file {filepath} has invalid connections! Aborting sync.")
        print("  Missing sources:", missing_sources)
        print("  Missing targets:", missing_targets)
        return False

    # Check for character corruption in file
    corrupted = [n for n in node_names if '??' in n or '\ufffd' in n]
    if corrupted:
        print(f"ERROR: Local file {filepath} has corrupted characters: {corrupted}")
        return False

    nodes_json = json.dumps(nodes, ensure_ascii=False)
    conn_json = json.dumps(connections, ensure_ascii=False)
    settings_json = json.dumps(settings, ensure_ascii=False)
    meta_json = json.dumps(meta, ensure_ascii=False)

    sql = f"""SET client_encoding = 'UTF8';
BEGIN;

-- 1. Insert into workflow_history
INSERT INTO workflow_history (
    "versionId",
    "workflowId",
    "name",
    "nodes",
    "connections",
    "nodeGroups",
    "authors",
    "description",
    "autosaved",
    "createdAt",
    "updatedAt"
) VALUES (
    '{new_version_id}',
    '{wf_id}',
    $NAME${name}$NAME$,
    $NODES${nodes_json}$NODES$,
    $CONN${conn_json}$CONN$,
    '[]'::json,
    'gabrielbassani03@gmail.com',
    '',
    false,
    NOW(),
    NOW()
);

-- 2. Upsert into workflow_published_version
INSERT INTO workflow_published_version (
    "workflowId",
    "publishedVersionId",
    "createdAt",
    "updatedAt"
) VALUES (
    '{wf_id}',
    '{new_version_id}',
    NOW(),
    NOW()
) ON CONFLICT ("workflowId") DO UPDATE SET
    "publishedVersionId" = EXCLUDED."publishedVersionId",
    "updatedAt" = NOW();

-- 3. Update workflow_entity (draft + active published pointer)
UPDATE workflow_entity
SET name = $NAME${name}$NAME$,
    nodes = $NODES${nodes_json}$NODES$,
    connections = $CONN${conn_json}$CONN$,
    settings = $SETTINGS${settings_json}$SETTINGS$,
    meta = $META${meta_json}$META$,
    "versionId" = '{new_version_id}',
    "activeVersionId" = '{new_version_id}',
    active = true,
    "isArchived" = false,
    "updatedAt" = NOW()
WHERE id = '{wf_id}';

-- 4. Record publication in history
INSERT INTO workflow_publish_history (
    "workflowId",
    "versionId",
    "event",
    "userId",
    "createdAt"
) VALUES (
    '{wf_id}',
    '{new_version_id}',
    'activated',
    '7c76ab62-355a-4b74-baf2-2eff6b8fe379',
    NOW()
);

COMMIT;
"""
    out, err = query_db(sql)
    if 'COMMIT' not in out and 'COMMIT' not in err:
        print(f"Failed to publish {wf_id}. Out: {out}, Err: {err}")
        return False

    print(f"Successfully published {wf_id} ('{name}') -> version {new_version_id} ({len(nodes)} nodes, {len(connections)} connections).")
    return True

def validate_all_in_db():
    print("\n=======================================================")
    print("VALIDATING PUBLISHED WORKFLOWS IN N8N DATABASE")
    print("=======================================================")
    
    # Query all active workflows
    sql = """
    SET client_encoding = 'UTF8'; 
    SELECT 
        w.id, 
        w.name, 
        w.active, 
        w."activeVersionId", 
        pv."publishedVersionId",
        (h."versionId" IS NOT NULL) as in_history
    FROM workflow_entity w
    LEFT JOIN workflow_published_version pv ON w.id = pv."workflowId"
    LEFT JOIN workflow_history h ON pv."publishedVersionId" = h."versionId"
    ORDER BY w.id;
    """
    out, _ = query_db(sql)
    all_valid = True

    for line in out.strip().split('\n'):
        if not line: continue
        parts = line.split('|')
        if len(parts) < 6: continue
        wf_id, name, active, active_vid, pub_vid, in_hist = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        
        # Only validate active ones
        if active != 't':
            continue

        if not pub_vid or not active_vid or active_vid != pub_vid or in_hist != 't':
            print(f"[FAIL] {wf_id} ({name}): Publication mismatch! active_vid={active_vid}, pub_vid={pub_vid}, in_hist={in_hist}")
            all_valid = False
            continue

        # Load published nodes and connections directly from workflow_history
        nodes_raw, _ = query_db(f"SELECT nodes FROM workflow_history WHERE \"versionId\" = '{pub_vid}';")
        conn_raw, _ = query_db(f"SELECT connections FROM workflow_history WHERE \"versionId\" = '{pub_vid}';")
        
        try:
            nodes = json.loads(nodes_raw.strip())
            connections = json.loads(conn_raw.strip())
        except Exception as e:
            print(f"[FAIL] {wf_id} ({name}): JSON parse error in workflow_history: {e}")
            all_valid = False
            continue

        node_names = set(n.get('name') for n in nodes)
        corrupted_nodes = [n for n in node_names if '??' in n or '\ufffd' in n]
        corrupted_conns = [k for k in connections if '??' in k or '\ufffd' in k]

        missing_sources = []
        missing_targets = []
        for s_node, outputs in connections.items():
            if s_node not in node_names:
                missing_sources.append(s_node)
            for _, c_groups in outputs.items():
                for c_group in c_groups:
                    for c in c_group:
                        t_node = c.get('node')
                        if t_node not in node_names:
                            missing_targets.append((s_node, t_node))

        has_error = bool(corrupted_nodes or corrupted_conns or missing_sources or missing_targets)
        if has_error:
            all_valid = False
            print(f"[FAIL] {wf_id} ({name}):")
            if corrupted_nodes: print(f"   Corrupted node names: {corrupted_nodes}")
            if corrupted_conns: print(f"   Corrupted conn keys: {corrupted_conns}")
            if missing_sources: print(f"   Missing source nodes: {missing_sources}")
            if missing_targets: print(f"   Missing target nodes: {missing_targets}")
        else:
            print(f"[OK] {wf_id} ({name}): PUBLISHED & VALID! Version: {pub_vid[:8]}... ({len(nodes)} nodes, {len(connections)} connections)")

    return all_valid

def main():
    # Sync and publish all 8 active production workflows
    for wf_id, filepath in ACTIVE_WORKFLOW_FILES.items():
        if not os.path.exists(filepath):
            print(f"ERROR: {filepath} not found!")
            sys.exit(1)
        ok = sync_and_publish_workflow(wf_id, filepath)
        if not ok:
            print(f"Aborting due to error syncing/publishing {wf_id}")
            sys.exit(1)

    all_valid = validate_all_in_db()
    if not all_valid:
        print("\nERROR: Some workflows failed validation in DB!")
        sys.exit(1)
    else:
        print("\n>>> ALL ACTIVE WORKFLOWS ARE 100% PUBLISHED AND VALID IN THE DATABASE! <<<")

if __name__ == '__main__':
    main()
