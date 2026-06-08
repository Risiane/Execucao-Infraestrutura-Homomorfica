import os
import json
import csv
import boto3
import tenseal as ts

ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localstack:4566")
BUCKET = os.getenv("BUCKET_NAME", "he-bucket")

# Caminho onde o cliente salvou o contexto com chave secreta.
SECRET_CONTEXT_PATH = "/tmp/he_secret_context.tenseal"

OUTPUT_JSON = "/app/output/resultados_finais.json"
OUTPUT_CSV = "/app/output/resultados_finais.csv"

def s3_client():
    # Cliente S3 usando o LocalStack.
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1"
    )

def get_object_bytes(s3, key):
    response = s3.get_object(Bucket=BUCKET, Key=key)
    return response["Body"].read()

def main():
    print("[CLIENTE] Iniciando download do resultado criptografado...")

    if not os.path.exists(SECRET_CONTEXT_PATH):
        raise FileNotFoundError(
            "Contexto secreto nao encontrado. Execute primeiro client_encrypt_upload.py no container cliente."
        )

    # Carrega o contexto secreto que ficou somente no cliente.
    with open(SECRET_CONTEXT_PATH, "rb") as f:
        secret_context = ts.context_from(f.read())

    s3 = s3_client()

    result_manifest_bytes = get_object_bytes(s3, "manifest/result_manifest.json")
    result_manifest = json.loads(result_manifest_bytes.decode("utf-8"))

    final_results = {}

    print("\nREGIAO | SOMA | QUANTIDADE | MEDIA")
    print("----------------------------------")

    for region, data in result_manifest["resultados"].items():
        result_key = data["ciphertext_resultado"]
        quantidade = data["quantidade"]

        # Baixa o resultado ainda criptografado.
        encrypted_result_bytes = get_object_bytes(s3, result_key)

        # Recria o vetor criptografado usando o contexto secreto do cliente.
        encrypted_result = ts.bfv_vector_from(secret_context, encrypted_result_bytes)

        # Somente o cliente descriptografa o resultado final.
        soma = int(encrypted_result.decrypt()[0])
        media = soma / quantidade

        final_results[region] = {
            "soma": soma,
            "quantidade": quantidade,
            "media": media
        }

        print(f"{region:<6} | {soma:<4} | {quantidade:<10} | {media:.2f}")

    os.makedirs("/app/output", exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=4, ensure_ascii=False)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Regiao", "Soma", "Quantidade", "Media"])

        for region, values in final_results.items():
            writer.writerow([
                region,
                values["soma"],
                values["quantidade"],
                values["media"]
            ])

    print(f"\n[CLIENTE] Resultado final salvo em: {OUTPUT_JSON}")
    print(f"[CLIENTE] Resultado final salvo em: {OUTPUT_CSV}")
    print("[CLIENTE] Descriptografia final concluida somente no cliente.")

if __name__ == "__main__":
    main()
