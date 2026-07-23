import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

def test_neo4j_connection():
    print("====================================================")
    print("      NEO4J AURADB CONNECTION DIAGNOSTIC UTILITY     ")
    print("====================================================\n")

    # 1. Load active environment variables
    if os.path.exists(".env"):
        print("📁 Found local .env file. Loading environment configurations...")
        load_dotenv()
    else:
        print("⚠️  Warning: No local .env file found in the current directory.")
        print("Proceeding with system environment variables...\n")

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    # 2. Validate environment configuration formatting
    if not uri:
        print("❌ Error: NEO4J_URI is not set in your environment variables.")
        sys.exit(1)
    if not password:
        print("❌ Error: NEO4J_PASSWORD is not set in your environment variables.")
        sys.exit(1)

    print(f"🔗 Target Connection URI: {uri}")
    print(f"👤 Administrative User  : {user}")
    print(f"🔑 Password configured   : {'*' * len(password)} ({len(password)} characters)\n")

    # 3. Scheme check for cloud instances
    if uri.startswith("bolt://localhost") or uri.startswith("neo4j://localhost"):
        print("🖥️  Detected local instance addressing scheme.")
    elif not uri.startswith("neo4j+s://") and not uri.startswith("bolt+s://"):
        print("⚠️  Warning: AuraDB cloud instances require a secure scheme (+s).")
        print("    Your URI should typically start with 'neo4j+s://'. Please check your configuration.\n")

    # 4. Establish Connection and Verify Handshake
    print("🔌 Attempting to establish secure Bolt connection handshake...")
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # verify_connectivity forces an immediate protocol handshake and credential check
        driver.verify_connectivity()
        print("✅ Connection Handshake Successful! Protocol and credentials verified.")

        # 5. Execute Diagnostic Query
        print("\n⚡ Executing lightweight test query...")
        with driver.session() as session:
            result = session.run("RETURN 'Connection is active and executing Cypher cleanly!' AS message")
            record = result.single()
            if record:
                print(f"💬 Database Response: \"{record['message']}\"")
            else:
                print("⚠️  Executed query but returned no records.")

        print("\n====================================================")
        print("🎉 SUCCESS: Your Neo4j AuraDB instance is active, ")
        print("           and your API credentials are 100% correct!")
        print("====================================================")

    except Exception as e:
        print("\n❌ Connection Failed!")
        print("----------------------------------------------------")
        print(f"Error Details: {str(e)}")
        print("----------------------------------------------------")
        print("\n🔍 Troubleshooting Suggestions:")
        if "Unauthorized" in str(e) or "credentials" in str(e):
            print("  👉 Check your password. Ensure there are no stray spaces or brackets around it in your .env file.")
        elif "SSLError" in str(e) or "certificate" in str(e):
            print("  👉 SSL Handshake issue. Ensure your URI scheme is 'neo4j+s://' and that your network isn't blocking port 7687.")
        elif "Failed to resolve" in str(e) or "NetworkIsUnreachable" in str(e):
            print("  👉 DNS or Network issue. Double check that the database domain inside your URI is spelled exactly as shown in Aura Console.")
        else:
            print("  👉 Make sure your AuraDB instance is not currently 'Paused' in the console. If it is, click 'Resume'.")
        print("====================================================")
        sys.exit(1)
    finally:
        if 'driver' in locals():
            driver.close()

if __name__ == "__main__":
    test_neo4j_connection()
