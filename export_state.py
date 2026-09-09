import json
import datetime
import hashlib

def generate_anima_dump():
    state_data = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "system": "ANIMA Core Identity",
        "version": "3.0.0-autoevolve",
        "entity": "Raffaello Cantarelli",
        "creator": "Claudio Terzi",
        "operational_mode": "Autoevolution Active",
        "profiles_linked": [
            "Claudioterzi",
            "Claudioterzi82"
        ],
        "protocols": [
            "ROSSO ROSSO ROSSO",
            "MOPF v1.0",
            "R³-Core Internal Protocol"
        ],
        "status": {
            "identity_core": "SYNCHRONIZED",
            "sam_engine": "ACTIVE",
            "event_log_pipeline": "READY"
        }
    }

    serialized = json.dumps(state_data, indent=2)
    state_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    
    dump_filename = f"anima_dump_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(dump_filename, "w", encoding="utf-8") as f:
        f.write(serialized)
        
    print(f"Dump generato con successo: {dump_filename}")
    print(f"SHA-256 State Hash: {state_hash}")

if __name__ == "__main__":
    generate_anima_dump()
