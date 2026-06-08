import os
import json
import boto3
import tenseal as ts

ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localstack:4566")
BUCKET = os.getenv("BUCKET_NAME", "he-bucket")

def s3_client():
    # Cliente S3 usando o LocalStack como nuvem simulada.
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1"
    )

def get_object_bytes(s3, key):
    # Baixa um objeto do bucket e retorna seu conteúdo em bytes.
    response = s3.get_object(Bucket=BUCKET, Key=key)
    return response["Body"].read()

def main():
    print("[SERVIDOR] Iniciando processamento homomorfico...")

    s3 = s3_client()

    # O servidor baixa apenas o contexto público.
    public_context_bytes = get_object_bytes(s3, "context/public_context.tenseal")
    context = ts.context_from(public_context_bytes)

    print("[SERVIDOR] Contexto publico carregado.")
    print("[SERVIDOR] Nenhuma chave secreta foi recebida.")

    # Baixa o manifesto para saber quais ciphertexts somar por região.
    manifest_bytes = get_object_bytes(s3, "manifest/input_manifest.json")
    manifest = json.loads(manifest_bytes.decode("utf-8"))

    result_manifest = {
        "descricao": "Resultado criptografado gerado pelo servidor",
        "observacao": "O servidor realizou soma homomorfica sem descriptografar os valores.",
        "resultados": {}
    }

    for region, items in manifest["regioes"].items():
        encrypted_sum = None

        print(f"[SERVIDOR] Processando regiao: {region}")

        for item in items:
            ciphertext_key = item["ciphertext"]

            # Baixa o ciphertext do bucket.
            encrypted_bytes = get_object_bytes(s3, ciphertext_key)

            # Recria o vetor criptografado usando o contexto público.
            encrypted_value = ts.bfv_vector_from(context, encrypted_bytes)

            # Soma homomórfica: o servidor soma sem ver os valores em claro.
            if encrypted_sum is None:
                encrypted_sum = encrypted_value
            else:
                encrypted_sum += encrypted_value

            print(f"[SERVIDOR] Ciphertext processado: {ciphertext_key}")

        result_key = f"result/{region}_soma_criptografada.tenseal"

        # Envia de volta apenas o resultado ainda criptografado.
        s3.put_object(
            Bucket=BUCKET,
            Key=result_key,
            Body=encrypted_sum.serialize()
        )

        result_manifest["resultados"][region] = {
            "quantidade": len(items),
            "ciphertext_resultado": result_key
        }

        print(f"[SERVIDOR] Resultado criptografado enviado: {result_key}")

    s3.put_object(
        Bucket=BUCKET,
        Key="manifest/result_manifest.json",
        Body=json.dumps(result_manifest, indent=4, ensure_ascii=False).encode("utf-8")
    )

    print("[SERVIDOR] Processamento finalizado.")
    print("[SERVIDOR] Resultado permanece criptografado no bucket.")

if __name__ == "__main__":
    main()
