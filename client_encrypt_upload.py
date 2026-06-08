import os
import json
import boto3
import tenseal as ts
from botocore.exceptions import ClientError

# Endpoint do LocalStack e nome do bucket vêm das variáveis do docker-compose.yml
ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localstack:4566")
BUCKET = os.getenv("BUCKET_NAME", "he-bucket")

# A chave secreta ficará somente dentro do container do cliente.
# Ela NÃO será enviada ao bucket e NÃO será salva na pasta compartilhada do projeto.
SECRET_CONTEXT_PATH = "/tmp/he_secret_context.tenseal"

# Dados de entrada do laboratório.
# Os valores serão criptografados antes de sair do cliente.
DATA = {
    "Norte": [40, 50],
    "Sul": [30, 60, 45],
    "Leste": [35, 42, 28]
}

def s3_client():
    # Cliente S3 apontando para o LocalStack, não para a AWS real.
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1"
    )

def ensure_bucket(s3):
    # Garante que o bucket exista antes do upload.
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=BUCKET)

def main():
    print("[CLIENTE] Iniciando geração do contexto criptográfico BFV...")

    # BFV foi escolhido por trabalhar bem com números inteiros.
    # plain_modulus define o espaço dos inteiros usados nas operações.
    context = ts.context(
        ts.SCHEME_TYPE.BFV,
        poly_modulus_degree=4096,
        plain_modulus=1032193
    )

    # Serializa o contexto com chave secreta apenas dentro do container cliente.
    secret_context = context.serialize(save_secret_key=True)
    with open(SECRET_CONTEXT_PATH, "wb") as f:
        f.write(secret_context)

    print(f"[CLIENTE] Chave/contexto secreto salvo somente em: {SECRET_CONTEXT_PATH}")

    s3 = s3_client()
    ensure_bucket(s3)

    manifest = {
        "descricao": "Manifesto com localização dos valores criptografados",
        "observacao": "Somente os valores numericos foram criptografados; regioes e quantidades sao metadados.",
        "regioes": {}
    }

    print("[CLIENTE] Criptografando valores inteiros e enviando ao bucket...")

    for region, values in DATA.items():
        manifest["regioes"][region] = []

        for index, value in enumerate(values, start=1):
            # Cada valor é criptografado individualmente.
            encrypted_value = ts.bfv_vector(context, [value])

            object_key = f"encrypted/{region}/valor_{index}.tenseal"

            # Envia somente o ciphertext para o bucket.
            s3.put_object(
                Bucket=BUCKET,
                Key=object_key,
                Body=encrypted_value.serialize()
            )

            manifest["regioes"][region].append({
                "indice": index,
                "ciphertext": object_key
            })

            print(f"[CLIENTE] Valor da regiao {region} indice {index} criptografado e enviado: {object_key}")

    # Depois de criptografar, o contexto é tornado público.
    # Assim, o servidor consegue operar sobre ciphertexts, mas não consegue descriptografar.
    context.make_context_public()
    public_context = context.serialize(save_secret_key=False)

    s3.put_object(
        Bucket=BUCKET,
        Key="context/public_context.tenseal",
        Body=public_context
    )

    s3.put_object(
        Bucket=BUCKET,
        Key="manifest/input_manifest.json",
        Body=json.dumps(manifest, indent=4, ensure_ascii=False).encode("utf-8")
    )

    print("[CLIENTE] Contexto publico enviado ao bucket.")
    print("[CLIENTE] Manifesto enviado ao bucket.")
    print("[CLIENTE] Upload concluido sem envio da chave secreta.")

if __name__ == "__main__":
    main()
