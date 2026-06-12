import sys
import os
sys.path.append(os.path.abspath("backend"))

from backend.app.services.scanner.scanner_service import ScannerService

def run():
    print("Running scanner on c:/git/lineage_explorer...")
    summary = ScannerService().scan_directory("c:/git/lineage_explorer", load_to_neo4j=True)
    print("Scan status:", summary.status)
    print("Loaded to Neo4j:", summary.loaded_to_neo4j)
    print("Tables:", summary.tables)
    print("SQL Scripts:", summary.sql_files)
    print("Shell Scripts:", summary.shell_scripts)
    print("Cron Jobs:", summary.cron_jobs)
    print("Relationships:", summary.relationships)
    print("Errors:", summary.errors)

if __name__ == "__main__":
    run()
