import os
import sys
import time
import traceback

from dotenv import load_dotenv
from openai import OpenAI


print("=" * 70)
print("MODULE 1 - NVIDIA NeMoTron API TEST")
print("=" * 70)


# ---------------------------------------------------------
# STEP 1: Load .env
# ---------------------------------------------------------

print("\n[1] Loading environment variables...")

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")

if api_key:
    print("    NVIDIA_API_KEY found: YES")
    print(f"    API key length: {len(api_key)} characters")
    print(f"    API key starts with: {api_key[:5]}*****")
else:
    print("    NVIDIA_API_KEY found: NO")
    print("    ERROR: Check your .env file.")
    sys.exit(1)


# ---------------------------------------------------------
# STEP 2: Configuration
# ---------------------------------------------------------

print("\n[2] Configuration")

BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_NAME = "nvidia/nemotron-3-ultra-550b-a55b"

print(f"    Base URL : {BASE_URL}")
print(f"    Model    : {MODEL_NAME}")


# ---------------------------------------------------------
# STEP 3: Create OpenAI client
# ---------------------------------------------------------

print("\n[3] Creating OpenAI client...")

try:
    client = OpenAI(
        base_url=BASE_URL,
        api_key=api_key,
    )

    print("    Client created successfully.")

except Exception as e:
    print("    FAILED to create client.")
    print(f"    Error type: {type(e).__name__}")
    print(f"    Error: {e}")
    traceback.print_exc()
    sys.exit(1)


# ---------------------------------------------------------
# STEP 4: Test connection by listing models
# ---------------------------------------------------------

print("\n[4] Testing connection to NVIDIA...")
print("    Calling /v1/models ...")

try:
    start_time = time.time()

    models = client.models.list()

    elapsed = time.time() - start_time

    print(f"    Connection successful! ({elapsed:.2f}s)")
    print(f"    Number of models returned: {len(models.data)}")

    print("\n    Available models:")

    for model in models.data:
        print(f"      - {model.id}")

except Exception as e:
    elapsed = time.time() - start_time

    print(f"    CONNECTION FAILED ({elapsed:.2f}s)")
    print(f"    Error type: {type(e).__name__}")
    print(f"    Error: {e}")

    print("\n    Full traceback:")
    traceback.print_exc()

    print("\n" + "=" * 70)
    print("MODEL LIST TEST FAILED")
    print("=" * 70)

    sys.exit(1)


# ---------------------------------------------------------
# STEP 5: Test whether requested model exists
# ---------------------------------------------------------

print("\n[5] Checking requested model...")

available_models = [model.id for model in models.data]

if MODEL_NAME in available_models:
    print("    Requested model FOUND!")
else:
    print("    WARNING: Requested model was NOT found in /v1/models.")
    print("\n    Requested:")
    print(f"      {MODEL_NAME}")

    print("\n    Available models:")
    for model in available_models:
        print(f"      {model.id}")

    print("\n    Do NOT continue until the model name is correct.")


# ---------------------------------------------------------
# STEP 6: Chat completion
# ---------------------------------------------------------

print("\n[6] Sending test chat completion...")

test_prompt = "Say 'Hello World' and then give me one short sentence introducing yourself."

print(f"    Prompt: {test_prompt}")
print("    Waiting for model response...")

try:
    start_time = time.time()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": test_prompt,
            }
        ],
        temperature=0.2,
        max_tokens=100,
    )

    elapsed = time.time() - start_time

    print(f"\n    Request successful! ({elapsed:.2f}s)")

    # -----------------------------------------------------
    # STEP 7: Inspect response
    # -----------------------------------------------------

    print("\n[7] Response information")

    print(f"    Response ID : {response.id}")
    print(f"    Object      : {response.object}")
    print(f"    Model       : {response.model}")

    if response.choices:
        choice = response.choices[0]

        print(f"    Finish reason: {choice.finish_reason}")
        print(f"    Choice index : {choice.index}")

        print("\n    Assistant response:")
        print("    " + "-" * 50)
        print(f"    {choice.message.content}")
        print("    " + "-" * 50)

    # -----------------------------------------------------
    # STEP 8: Token usage
    # -----------------------------------------------------

    print("\n[8] Token usage")

    if response.usage:
        print(f"    Prompt tokens     : {response.usage.prompt_tokens}")
        print(f"    Completion tokens : {response.usage.completion_tokens}")
        print(f"    Total tokens      : {response.usage.total_tokens}")
    else:
        print("    Usage information not returned.")

except Exception as e:

    print("\n    CHAT COMPLETION FAILED")
    print(f"    Error type: {type(e).__name__}")
    print(f"    Error: {e}")

    print("\n    Full traceback:")
    traceback.print_exc()

    sys.exit(1)


# ---------------------------------------------------------
# FINAL
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("MODULE 1 NVIDIA API TEST PASSED")
print("=" * 70)
print("Environment      : OK")
print("API key          : FOUND")
print("API connection   : OK")
print("Model             : OK")
print("Chat completion  : OK")
print("=" * 70)