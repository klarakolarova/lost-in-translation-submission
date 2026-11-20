"""Optionally regenerate German translations for the fixed French sample.

Use the saved model settings and the GGUF model's embedded prompt template.
Save each attempt separately from the submitted translations and resume from
that checkpoint when rerun. Failed attempts remain recorded and are not retried.

Run python scripts/translate_sample.py --help for setup and output locations.
"""

# Import tools for command-line help, saved inputs and generation timing.
import argparse
from pathlib import Path
from time import perf_counter
import json

# Locate the model and sample relative to the project.
ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "translategemma-4b-it-Q4_K_M.gguf"


# Replace the checkpoint only after the complete updated JSON has been written.
def save_checkpoint(output: dict, output_path: Path) -> None:
    temporary_path = output_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary_path.replace(output_path)


# Translate pending sample texts and checkpoint every completed or failed attempt.
def translate(
    project_dir: Path,
    input_name: str = "validated_sample.json",
    output_name: str = "translations_rerun.json",
    record_over_limit: bool = False,
) -> None:
    data = json.loads(
        (project_dir / "results/data" / input_name).read_text(encoding="utf-8")
    )
    model_path = project_dir / "models" / MODEL_NAME
    output_path = project_dir / "results/data" / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "model_file": model_path.name,
        "settings": {
            "temperature": 0.0,
            "max_tokens": 1800,
            "n_ctx": 4096,
            "seed": 42,
            "repeat_penalty": 1.0,
        },
        "source_language": "fr",
        "target_language": "de",
        "records": [],
        "failed_records": [],
    }

    # Resume saved attempts only when their inputs and settings match
    if output_path.exists():
        saved = json.loads(output_path.read_text(encoding="utf-8"))
        for key in ("model_file", "settings", "source_language", "target_language"):
            if saved[key] != output[key]:
                raise ValueError(f"Saved {key} differs; use a separate output file.")
        inputs = {record["document_id"]: record for record in data["records"]}
        for record in saved["records"] + saved.get("failed_records", []):
            original = inputs[record["document_id"]]
            if any(record[key] != value for key, value in original.items()):
                raise ValueError(f"Input changed for {record['document_id']}.")
        for record in saved["records"]:
            if record["finish_reason"] != "stop" or not record["translation_de"]:
                raise ValueError(
                    f"Inspect incomplete document {record['document_id']} before resuming."
                )
        saved.setdefault("failed_records", [])
        output = saved
    attempted_ids = {
        record["document_id"] for record in output["records"] + output["failed_records"]
    }
    pending_records = [
        record
        for record in data["records"]
        if record["document_id"] not in attempted_ids
    ]
    print(
        f"  Sample: {len(data['records'])}; already attempted: {len(attempted_ids)}; "
        f"remaining: {len(pending_records)}.",
        flush=True,
    )
    if not pending_records:
        print(
            f"  No pending texts. Completed: {len(output['records'])}; "
            f"failed: {len(output['failed_records'])}."
        )
        print(f"  Data: {output_path}")
        return

    if not model_path.is_file():
        raise SystemExit(
            f"Model not found: {model_path}\n"
            "Download the GGUF file listed under Optional regeneration in README.md "
            "and place it in models/."
        )
    # Load optional dependencies only when generation is needed, so --help works without them.
    try:
        from jinja2.sandbox import ImmutableSandboxedEnvironment
        from llama_cpp import Llama
    except ImportError as error:
        raise SystemExit(
            "Translation dependencies are missing. Run:\n"
            "  python -m pip install -r requirements-translation.txt"
        ) from error

    print(
        "  Loading TranslateGemma 4B; generation time depends on your hardware...",
        flush=True,
    )
    model = Llama(
        model_path=str(model_path), n_ctx=4096, n_gpu_layers=-1, seed=42, verbose=False
    )
    template = ImmutableSandboxedEnvironment().from_string(
        model.metadata["tokenizer.chat_template"]
    )

    # Render the model's own translation prompt for each full text
    for position, record in enumerate(pending_records, start=1):
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "source_lang_code": "fr",
                        "target_lang_code": "de",
                        "text": record["input_fr"],
                    }
                ],
            }
        ]
        prompt = template.render(
            messages=messages, bos_token="<bos>", add_generation_prompt=True
        )
        prompt_tokens = model.tokenize(
            prompt.encode("utf-8"), add_bos=False, special=True
        )
        if len(prompt_tokens) > 2048:
            if not record_over_limit:
                raise ValueError(
                    f"Document {record['document_id']} exceeds the 2048-token input limit."
                )
            # Keep the fixed sample: record the document as a failure, never truncate or redraw
            output["failed_records"].append(
                {
                    **record,
                    "translation_de": "",
                    "prompt": prompt,
                    "finish_reason": "input_over_limit",
                    "usage": {"prompt_tokens": len(prompt_tokens)},
                    "generation_seconds": 0.0,
                }
            )
            save_checkpoint(output, output_path)
            print(
                f"Flagged over input limit ({len(prompt_tokens)} tokens): {record['document_id']}",
                flush=True,
            )
            continue

        # Generate without showing the model the German reference
        print(
            f"  [{position}/{len(pending_records)}] Translating motion {record['document_id']}...",
            flush=True,
        )
        generation_start = perf_counter()
        response = model.create_completion(
            prompt=prompt_tokens,
            temperature=0.0,
            max_tokens=1800,
            repeat_penalty=1.0,
            stop=["<end_of_turn>", "<eos>"],
        )
        choice = response["choices"][0]
        result = {
            **record,
            "translation_de": choice["text"].strip(),
            "prompt": prompt,
            "finish_reason": choice["finish_reason"],
            "usage": response["usage"],
            "generation_seconds": perf_counter() - generation_start,
        }
        failed = choice["finish_reason"] != "stop" or not result["translation_de"]
        destination = "failed_records" if failed else "records"
        output[destination].append(result)

        # Save every attempt and keep failed outputs separate for inspection
        save_checkpoint(output, output_path)
        status = "Flagged incomplete" if failed else "Saved"
        print(f"    {status}: {record['document_id']}", flush=True)

    print(
        f"  Finished: {len(output['records'])} completed; {len(output['failed_records'])} failed."
    )
    print(f"  Data: {output_path}")
    print("  Submitted translations remain the inputs to reproduce.sh.")


# Explain prerequisites and run translation using the fixed sample and model settings.
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate translations for the fixed French sample using TranslateGemma 4B.",
        epilog=(
            "Setup: activate the project environment, install requirements-translation.txt, "
            "run classify_author_language.py and validate_sample.py, and place "
            f"{MODEL_NAME} in models/. See README.md for commands and the model link. "
            "Output: results/data/translations_rerun.json. Rerunning resumes unattempted "
            "texts; failed attempts are retained. Submitted inputs are not overwritten."
        ),
    )
    parser.parse_args()
    sample_path = ROOT / "results/data/validated_sample.json"
    if not sample_path.is_file():
        raise SystemExit(
            "The validated sample is missing. From the project root, run:\n"
            "  python scripts/classify_author_language.py\n"
            "  python scripts/validate_sample.py"
        )
    print("Optional translation regeneration", flush=True)
    print("  Input: results/data/validated_sample.json", flush=True)
    print(
        "  Output: results/data/translations_rerun.json (resumes saved attempts).",
        flush=True,
    )
    translate(ROOT, record_over_limit=True)


# Run optional generation when this file is executed directly.
if __name__ == "__main__":
    main()
